import multiprocessing  # For the multi-core processing
import hashlib          # Simple and quick implementation of MD5
import random           # Pseudo-random number generation
import string           # Contains prebuilt lists of ASCII/UTF-8 characters
import time             # For calculating when to print to console
import math             # Used to calculate how many stringFactories to build


# Basic input, prone to breaking
TARGET_LEN = int(input("Length of password: "))
THREAD_COUNT = int(input("Number of hashing threads: "))
TARGET_HASH = input("Target hash: ")

# Sub-function to generate a random string
def genRandString(length):
    return "".join(random.choices(string.ascii_letters + string.digits + string.punctuation, k = length))

# Shorthand function for generating MD5 hashes
def md5(inputString):
    return hashlib.md5(inputString.encode("utf-8")).hexdigest()

# Hasher's meat and potatoes
def hashProcess(sharedList, targetHash, processID, sharedValue):

    # Variable initialization
    currentStr = ""
    hashrate = 0
    bufferOutError = 0
    sharedValue.value = 0

    # Used for dual timers
    time1 = time.time()
    time2 = time1

    # While the current hash isn't the target hash and the target hash isn't found by another thread...
    while (md5(currentStr) != targetHash and sharedValue.value != 1):

        # Try to pull the first value from the buffer, add 1 to the hashrate, set the bufferOutError counter to 0
        try:
            currentStr = sharedList.pop(0)
            hashrate += 1
            bufferOutError = 0

        # If that fails, add 1 to the bufferOutError. If bufferOutError reaches 100, inform the user.
        except:
            bufferOutError += 1
            if (bufferOutError == 100):
                print("BUFF_ERR: Please report this error along with settings used to the Github repository.")
        
        # Every 10 seconds, print a status report in this format:
        # PID   HASH/S  BUFFERSIZE
        if (time.time() - time1 > 10):
            print(f"{processID}\t{hashrate/10}\t{len(sharedList)}")
            time1 = time.time()
            hashrate = 0
    
    # If the loop is broken and this process was the one that found the source...
    if (md5(currentStr) == targetHash):

        # Print a report in the following style:
        #   PID
        #   SOLUTION
        #   TIME TAKEN
        print(f"\t{processID}")
        print(f"\t{currentStr}")
        print(f"\t{time.time() - time2} seconds")

        # Set the sharedValue value to 1 to let everything else know that we're done here.
        sharedValue.value = 1
    
    # Return value for .join()
    return 0

# stringFactory, the most resource-intensive part of the process (Which is why it gets 2.5 times as many cores as the hash processes)
def stringFactory(sharedList, length, sharedValue):

    # Variable initiation
    newString = ""

    # Main loop, breaks when sharedValue's value is equal to one.
    while (sharedValue.value != 1):

        # Generate a random string of specified length
        newString = genRandString(length)

        # Duplicate avoidance, if the phrase is already in the list then skip.
        while (newString in sharedList):
            newString = genRandString(length)

        # Skips the currently generated string if the length of the buffer is greater than a thousand
        if (len(sharedList) < 1000):
            sharedList.append(newString)
    
    # Return value for .join()
    return 0

# The real meat and potatoes
if (__name__ == "__main__"):

    # Used for sharedValue and the buffer
    with multiprocessing.Manager() as manager:

        # Establish buffer
        passwdList = manager.list()

        # Establish sharedValue (Acts as a boolean)
        sharedValue = manager.Value("i", 0)

        # Create the string factory processes:
        # Target = stringFactory
        # Args = buffer, length, sharedValue
        # Create THREAD_COUNT * 2.5 of them, rounded up
        processes = [multiprocessing.Process(target = stringFactory, args=(passwdList, TARGET_LEN, sharedValue)) for i in range(math.ceil(THREAD_COUNT * 2.5))]

        # Essentially the same deal but for the hashers
        # Target = hashProcess
        # Args = buffer, target hash, PID, sharedValue
        # Create THREAD_COUNT of them
        processes2 = [multiprocessing.Process(target = hashProcess, args=(passwdList, TARGET_HASH, i, sharedValue)) for i in range(THREAD_COUNT)]

        # Start the stringFactories
        for process in processes:
            process.start()

        # Start the hashers
        for process in processes2:
            process.start()

        # Once the sharedValue is set to 1 and the functions return a value, kill the processes. Kill the hashers first.
        for process in processes2:
            process.join()

        # Kill the stringFactories second.
        for process in processes:
            process.join()
