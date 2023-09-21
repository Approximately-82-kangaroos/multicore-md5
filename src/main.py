import multiprocessing
import hashlib
import random
import string
import time
import math

TARGET_LEN = int(input("Length of password: "))
THREAD_COUNT = int(input("Number of hashing threads: "))
TARGET_HASH = input("Target hash: ")

def genRandString(length):
    return "".join(random.choices(string.ascii_letters + string.digits + string.punctuation, k = length))

def md5(inputString):
    return hashlib.md5(inputString.encode("utf-8")).hexdigest()

def hashProcess(sharedList, targetHash, processID, sharedValue):
    currentStr = ""
    time1 = time.time()
    time2 = time1
    hashrate = 0
    bufferOutError = 0
    sharedValue.value = 0
    while (md5(currentStr) != targetHash and sharedValue.value != 1):
        try:
            currentStr = sharedList.pop(0)
            hashrate += 1
            bufferOutError = 0
        except:
            bufferOutError += 1
            if (bufferOutError == 100):
                print("BUFF_ERR: Please report this error along with settings used to the Github repository.")
        if (time.time() - time1 > 10):
            print(f"{processID}\t{hashrate/10}\t{len(sharedList)}")
            time1 = time.time()
            hashrate = 0
    if (md5(currentStr) == targetHash):
        print(f"\t{processID}")
        print(f"\t{currentStr}")
        print(f"\t{time.time() - time2} seconds")
        sharedValue.value = 1
    return 0

def stringFactory(sharedList, length, sharedValue):
    newString = ""
    while (sharedValue.value != 1):
        newString = genRandString(length)
        while (newString in sharedList):
            newString = genRandString(length)
        if (len(sharedList) < 1000):
            sharedList.append(newString)
    return 0

if (__name__ == "__main__"):
    with multiprocessing.Manager() as manager:
        passwdList = manager.list()
        sharedValue = manager.Value("i", 0)
        processes = [multiprocessing.Process(target=stringFactory, args=(passwdList, TARGET_LEN, sharedValue)) for i in range(math.ceil(THREAD_COUNT * 2.5))]
        processes2 = [multiprocessing.Process(target=hashProcess, args=(passwdList, TARGET_HASH, i, sharedValue)) for i in range(THREAD_COUNT)]
        for process in processes:
            process.start()

        for process in processes2:
            process.start()

        for process in processes2:
            process.join()

        for process in processes:
            process.join()
