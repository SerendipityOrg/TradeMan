# Keep module imports prior to classes
import multiprocessing
from tabulate import tabulate
from time import sleep
from datetime import datetime
import pandas as pd
import numpy as np
import urllib
import argparse
from alive_progress import alive_bar
from classes.Changelog import VERSION
from classes.ParallelProcessing import StockConsumer
from classes.CandlePatterns import CandlePatterns
from classes.OtaUpdater import OTAUpdater
from classes.ColorText import colorText
import classes.Utility as Utility
import classes.Screener as Screener
import classes.ConfigManager as ConfigManager
import classes.Fetcher as Fetcher
import sys
import platform
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
multiprocessing.freeze_support()

# Argument Parsing for test purpose
argParser = argparse.ArgumentParser()
argParser.add_argument('-t', '--testbuild', action='store_true',
                       help='Run in test-build mode', required=False)
argParser.add_argument('-d', '--download', action='store_true',
                       help='Only Download Stock data in .pkl file', required=False)
# Dummy Arg for pytest -v
argParser.add_argument('-v', action='store_true')
args = argParser.parse_args()

# Try Fixing bug with this symbol
TEST_STKCODE = "SBIN"

# Constants
np.seterr(divide='ignore', invalid='ignore')

# Global Variabls
screenCounter = None
screenResultsCounter = None
stockDict = None
keyboardInterruptEvent = None
loadedStockData = False
loadCount = 0
maLength = None
newlyListedOnly = False

configManager = ConfigManager.tools()
fetcher = Fetcher.tools(configManager)
screener = Screener.tools(configManager)
candlePatterns = CandlePatterns()

# Get system wide proxy for networking
try:
    proxyServer = urllib.request.getproxies()['http']
except KeyError:
    proxyServer = ""

# Manage Execution flow


def initExecution():
    global newlyListedOnly

    # Automatically setting tickerOption to 12 (All Stocks)
    tickerOption = 12

    # Automatically setting executeOption to 0 (Full Screening)
    executeOption = 0

    return tickerOption, executeOption


# Main function
def main(testing=False, testBuild=False, downloadOnly=False):
    global screenCounter, screenResultsCounter, stockDict, loadedStockData, keyboardInterruptEvent, loadCount, maLength, newlyListedOnly
    screenCounter = multiprocessing.Value('i', 1)
    screenResultsCounter = multiprocessing.Value('i', 0)
    keyboardInterruptEvent = multiprocessing.Manager().Event()

    if stockDict is None:
        stockDict = multiprocessing.Manager().dict()
        loadCount = 0

    screenResults = pd.DataFrame(columns=[
                                 'Stock', 'Consolidating', 'Breaking-Out', 'LTP', 'Volume', 'MA-Signal', 'RSI', 'Trend', 'Pattern'])
    saveResults = pd.DataFrame(columns=[
                               'Stock', 'Consolidating', 'Breaking-Out', 'LTP', 'Volume', 'MA-Signal', 'RSI', 'Trend', 'Pattern'])

    # Default values for the variables:
    reversalOption = None
    daysForLowestVolume = 30
    minRSI = 0
    maxRSI = 100
    respChartPattern = 1
    insideBarToLookback = 7

    if testBuild:
        tickerOption = 1
    elif downloadOnly:
        tickerOption = 12
    else:
        try:
            tickerOption, _ = initExecution()
        except KeyboardInterrupt:
            input(colorText.BOLD + colorText.FAIL +
                  "[+] Press any key to Exit!" + colorText.END)
            sys.exit(0)

    configManager.getConfig(ConfigManager.parser)
    try:
        if tickerOption == 'W':
            listStockCodes = fetcher.fetchWatchlist()
            if listStockCodes is None:
                input(colorText.BOLD + colorText.FAIL +
                      f'[+] Create the watchlist.xlsx file in {os.getcwd()} and Restart the Program!' + colorText.END)
                sys.exit(0)
        elif tickerOption == 'N':
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
            prediction = screener.getNiftyPrediction(
                data=fetcher.fetchLatestNiftyDaily(proxyServer=proxyServer),
                proxyServer=proxyServer
            )
            input('\nPress any key to Continue...\n')
            return
        elif tickerOption == 'E':
            result_df = pd.DataFrame(
                columns=['Time', 'Stock/Index', 'Action', 'SL', 'Target', 'R:R'])
            last_signal = {}
            first_scan = True
            result_df = screener.monitorFiveEma(        # Dummy scan to avoid blank table on 1st scan
                proxyServer=proxyServer,
                fetcher=fetcher,
                result_df=result_df,
                last_signal=last_signal
            )
            try:
                while True:
                    Utility.tools.clearScreen()
                    last_result_len = len(result_df)
                    result_df = screener.monitorFiveEma(
                        proxyServer=proxyServer,
                        fetcher=fetcher,
                        result_df=result_df,
                        last_signal=last_signal
                    )
                    print(colorText.BOLD + colorText.WARN + '[+] 5-EMA : Live Intraday Scanner \t' + colorText.END +
                          colorText.FAIL + f'Last Scanned: {datetime.now().strftime("%H:%M:%S")}\n' + colorText.END)
                    print(tabulate(result_df, headers='keys', tablefmt='psql'))
                    print('\nPress Ctrl+C to exit.')
                    if len(result_df) != last_result_len and not first_scan:
                        Utility.tools.alertSound(beeps=5)
                    sleep(60)
                    first_scan = False
            except KeyboardInterrupt:
                input('\nPress any key to Continue...\n')
                return
        else:
            listStockCodes = fetcher.fetchStockCodes(
                tickerOption, proxyServer=proxyServer)
    except urllib.error.URLError:
        print(colorText.BOLD + colorText.FAIL +
              "\n\n[+] Oops! It looks like you don't have an Internet connectivity at the moment! Press any key to exit!" + colorText.END)
        input('')
        sys.exit(0)

    if not Utility.tools.isTradingTime() and configManager.cacheEnabled and not loadedStockData and not testing:
        Utility.tools.loadStockData(stockDict, configManager, proxyServer)
        loadedStockData = True
    loadCount = len(stockDict)

    print(colorText.BOLD + colorText.WARN +
          "[+] Starting Stock Screening.. Press Ctrl+C to stop!\n")

    # Adjusting the items list for multiprocessing:
    items = [(len(listStockCodes), configManager, fetcher, screener, candlePatterns,
              stock, newlyListedOnly, downloadOnly) for stock in listStockCodes]

    tasks_queue = multiprocessing.JoinableQueue()
    results_queue = multiprocessing.Queue()

    totalConsumers = multiprocessing.cpu_count()
    if totalConsumers == 1:
        totalConsumers = 2      # This is required for single core machine
    if configManager.cacheEnabled is True and multiprocessing.cpu_count() > 2:
        totalConsumers -= 1
    consumers = [StockConsumer(tasks_queue, results_queue, screenCounter, screenResultsCounter, stockDict, proxyServer, keyboardInterruptEvent)
                 for _ in range(totalConsumers)]

    for worker in consumers:
        worker.daemon = True
        worker.start()

    if testing or testBuild:
        for item in items:
            tasks_queue.put(item)
            result = results_queue.get()
            if result is not None:
                screenResults = screenResults.append(
                    result[0], ignore_index=True)
                saveResults = saveResults.append(
                    result[1], ignore_index=True)
                if testing or (testBuild and len(screenResults) > 2):
                    break
    else:
        for item in items:
            tasks_queue.put(item)
        # Append exit signal for each process indicated by None
        for _ in range(multiprocessing.cpu_count()):
            tasks_queue.put(None)
        try:
            numStocks = len(listStockCodes)
            print(colorText.END+colorText.BOLD)
            bar, spinner = Utility.tools.getProgressbarStyle()
            with alive_bar(numStocks, bar=bar, spinner='dots') as progressbar:
                while numStocks:
                    result = results_queue.get()
                    if result is not None:
                        screenResults = screenResults.append(
                            result[0], ignore_index=True)
                        saveResults = saveResults.append(
                            result[1], ignore_index=True)
                    numStocks -= 1
                    progressbar.text(colorText.BOLD + colorText.GREEN +
                                     f'Found {screenResultsCounter.value} Stocks' + colorText.END)
                    progressbar()
        except KeyboardInterrupt:
            try:
                keyboardInterruptEvent.set()
            except KeyboardInterrupt:
                pass
            print(colorText.BOLD + colorText.FAIL +
                  "\n[+] Terminating Script, Please wait..." + colorText.END)
            for worker in consumers:
                worker.terminate()

    print(colorText.END)
    # Exit all processes. Without this, it threw error in next screening session
    for worker in consumers:
        try:
            worker.terminate()
        except OSError as e:
            if e.winerror == 5:
                pass

        # Flush the queue so depending processes will end
    from queue import Empty
    while True:
        try:
            _ = tasks_queue.get(False)
        except Exception as e:
            break

    screenResults.sort_values(by=['Stock'], ascending=True, inplace=True)
    saveResults.sort_values(by=['Stock'], ascending=True, inplace=True)
    screenResults.set_index('Stock', inplace=True)
    saveResults.set_index('Stock', inplace=True)
    screenResults.rename(
        columns={
            'Trend': f'Trend ({configManager.daysToLookback}Days)',
            'Breaking-Out': f'Breakout ({configManager.daysToLookback}Days)',
            'LTP': 'LTP (%% Chng)'
        },
        inplace=True
    )
    saveResults.rename(
        columns={
            'Trend': f'Trend ({configManager.daysToLookback}Days)',
            'Breaking-Out': f'Breakout ({configManager.daysToLookback}Days)',
        },
        inplace=True
    )

    screenResults = screenResults[screenResults['Volume'] >= 3]

    print(tabulate(screenResults, headers='keys', tablefmt='psql'))

    print(colorText.BOLD + colorText.GREEN +
          f"[+] Found {len(screenResults)} Stocks." + colorText.END)
    if configManager.cacheEnabled and not Utility.tools.isTradingTime() and not testing:
        print(colorText.BOLD + colorText.GREEN +
              "[+] Caching Stock Data for future use, Please Wait... " + colorText.END, end='')
        Utility.tools.saveStockData(
            stockDict, configManager, loadCount)

    Utility.tools.setLastScreenedResults(screenResults)
    if not testBuild and not downloadOnly:
        Utility.tools.promptSaveResults(saveResults)
        print(colorText.BOLD + colorText.WARN +
              "[+] Note: Trend calculation is based on number of days recent to screen as per your configuration." + colorText.END)
        print(colorText.BOLD + colorText.GREEN +
              "[+] Screening Completed! Press Enter to Continue.." + colorText.END)
        input('')
    newlyListedOnly = False


if __name__ == "__main__":
    Utility.tools.clearScreen()
    isDevVersion = OTAUpdater.checkForUpdate(proxyServer, VERSION)
    if not configManager.checkConfigFile():
        configManager.setConfig(ConfigManager.parser,
                                default=True, showFileCreatedText=False)
    if args.testbuild:
        print(colorText.BOLD + colorText.FAIL +
              "[+] Started in TestBuild mode!" + colorText.END)
        main(testBuild=True)
    elif args.download:
        print(colorText.BOLD + colorText.FAIL +
              "[+] Download ONLY mode! Stocks will not be screened!" + colorText.END)
        main(downloadOnly=True)
    else:
        try:
            while True:
                main()
        except Exception as e:
            raise e
            if isDevVersion == OTAUpdater.developmentVersion:
                raise (e)
            input(colorText.BOLD + colorText.FAIL +
                  "[+] Press any key to Exit!" + colorText.END)
            sys.exit(0)



