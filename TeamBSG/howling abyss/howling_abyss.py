import requests
import pandas as pd
import time
import json

# summonerId로 검색해 accountId를 찾는 메소드
def accountId_by_summonerId(summonerId):
    search_accountId = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/" + summonerId + "?api_key=" + api_key
    r = requests.get(search_accountId)

    if r.status_code == 200:
        pass

    elif r.status_code == 429:
        while True:
            if r.status_code == 429:
                print("search accountId by summonerId 429")
                time.sleep(5)

                r = requests.get(search_accountId)
            elif r.status_code == 200:
                print("recovered api")
                break
    elif r.status_code == 503:
        while True:
            if r.status_code == 503 or r.status_code == 429:
                print("search accountId by summonerId 503")
                time.sleep(5)
                r = requests.get(search_accountId)

            elif r.status_code == 200:
                print("recovery api")
                break
            else:
                print("search match by gameId", r.status_code)
                break
    elif r.status_code == 504:
        print("Gateway time out, reconnect...")
        r = requests.get(search_accountId)

    elif r.status_code == 403:
        print("please renewal api")
    else:
        print("state code", r.status_code)

    return r.json()['accountId']


# gameId로 검색해서 match 결과를 찾는 메소드
def match_by_gameId(gameId):
    search_match = "https://kr.api.riotgames.com/lol/match/v4/matches/" + str(gameId) + "?api_key=" + api_key
    r = requests.get(search_match)

    if r.status_code == 200:
        pass

    elif r.status_code == 429:
        while True:
            if r.status_code == 429:
                print("search match by gameId 429")
                time.sleep(5)

                r = requests.get(search_match)
            elif r.status_code == 200:
                print("recovery api")
                break
            else:
                print("search match by gameId", r.status_code)

    elif r.status_code == 503:
        while True:
            if r.status_code == 503 or r.status_code == 429:
                print("search match by gameId 503")
                time.sleep(5)
                r = requests.get(search_match)

            elif r.status_code == 200:
                print("recovery api")
                break

            else:
                print("search match by gameId", r.status_code)
                break
    elif r.status_code == 504:
        print("Gateway time out, reconnect...")
        r = requests.get(search_match)

    elif r.status_code == 403:
        print("please renewal api")

    else:
        print("state code", r.status_code)

    df = pd.DataFrame()

    # 매치에서 열명의 플레이어들의 챔피언 픽과 승패를 뽑아서 데이터프레임으로 만든뒤 df에 저장
    for i in range(10):
        try:
            raw_data = {'championId': r.json()['participants'][i]['championId'],
                        'win': r.json()['participants'][i]['stats']['win']}
            raw_data = pd.DataFrame([raw_data])
            df = pd.concat([df, raw_data])
        except:
            print("r.status_code: ", r.status_code)
            break
    return df


# accountId를 이용해 match lists를 찾아오는 메소드

def matchlists_by_accountId(accountId):
    search_matchlists = "https://kr.api.riotgames.com/lol/match/v4/matchlists/by-account/" + accountId + "?queue=450&season=13&api_key=" + api_key
    r = requests.get(search_matchlists)

    if r.status_code == 200:  # 정상 수행
        pass

    elif r.status_code == 429:  # 데이터 제한
        while True:
            if r.status_code == 429:  # 계속 제한이 걸릴 경우 5초 뒤에 다시 실행
                print("search match lists 429")
                time.sleep(5)

                r = requests.get(search_matchlists)
            elif r.status_code == 200:  # 정상 수행
                print("recovery api")
                break

    elif r.status_code == 503:
        print("search matchlists 503")
        while True:
            if r.status_code == 503 or r.status_code == 429:
                time.sleep(5)
                r = requests.get(search_matchlists)
            elif r.status_code == 200:
                print("recovery service")
                break
    elif r.status_code == 403:
        print("please renewal api")

    else:
        print("state code", r.status_code)
        pass

    df = pd.DataFrame()

    for i in range(len(r.json()['matches'])):
        gameId = r.json()['matches'][i]['gameId']

        raw_data = match_by_gameId(gameId)

        df = pd.concat([df, raw_data])

    return df


api_key = "RGAPI-9ed10019-6db9-4b4f-b02d-dc8ecf4e27a9"

#RANKED_SOLO grandmaster search
grandmaster = "https://kr.api.riotgames.com/lol/league/v4/grandmasterleagues/by-queue/RANKED_SOLO_5x5?api_key="+api_key

grandmaster = requests.get(grandmaster)

df = pd.DataFrame()
for i in range(len(grandmaster.json()['entries'])):
    cnt = 0
    # summonerId를 가져온다
    summonerId = grandmaster.json()['entries'][i]['summonerId']
    print("search summonerId complete")

    # summonerId를 바탕으로 accountId를 가져온다
    accountId = accountId_by_summonerId(summonerId)
    print("search accountId complete")

    # DataFrame으로 저장된 결과물("championId, win")
    raw_data = matchlists_by_accountId(accountId)
    print("search matchlists complete")

    df = pd.concat([df, raw_data])
    print("complete", i)
    df.to_csv("howling_abyss_result(grandmaster).csv", encoding="cp949")




df = pd.read_csv("howling_abyss_result(grandmaster).csv", encoding="cp949")

matches = {df["championId"][0]:{"total":0, "win":0, "lose":0}}
championId = df["championId"]
win = df["win"]

for i in range(len(df)):

    if championId[i] in matches:

        if win[i] == True:
            matches[championId[i]]["win"] = matches[championId[i]]["win"]+1
        else:
            matches[championId[i]]["lose"] = matches[championId[i]]["lose"]+1

        matches[championId[i]]["total"] = matches[championId[i]]["total"]+1

    else:
        matches[championId[i]] = {"total":1}

        if win[i] == True:
            matches[championId[i]]["win"] = 1
            matches[championId[i]]["lose"] = 0
        else:
            matches[championId[i]]["lose"] = 1
            matches[championId[i]]["win"] = 0

print(pd.DataFrame(matches))
pd.DataFrame(matches).to_csv("matches.csv", encoding="cp949")
