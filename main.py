import pandas as pd
import yfinance as yf  # 주가 데이터 받기위한 라이브러리
import quantstats as qs  # 리포트 형식으로 시각화해주는 라이브러리

# yahoo finance에서 필요 종목들의 공통 시작일부터 종가 데이터 받기
def get_adj_close_data(tickers, type="Adj Close"):
    df = yf.download(tickers)
    df = df[type]
    df.dropna(inplace=True)
    return df

def get_rebalance_date(df, rebal="month"):
    res_df = pd.DataFrame()
    df["year"] = df.index.year
    df["month"] = df.index.month
    df["day"] = df.index.day
    days_df = df.groupby(["year", "month"])["day"].max()
    for i in range(len(days_df)):
        if days_df.iloc[i] > 25:
            day = "{}-{}-{}".format(days_df.index[i][0], days_df.index[i][1], days_df.iloc[i])
            res_df = pd.concat([res_df, df[df.index == day]])
    return res_df

tickers_canary = ['SPY', 'VEA', 'VWO', 'AGG']
tickers_g4 = ["QQQ", "VEA", "VWO", "AGG"]
tickers_g12 = ['SPY', 'QQQ', 'IWM', 'IEV', 'EWY', 'VWO', 'RWX', 'DBC', 'GLD', 'HYG', 'LQD', 'TLT']
tickers_safe = ['BIL', 'IEF', 'TLT', 'AGG', 'LQD', 'TIP', 'DBC']
tickers_all = list(set(tickers_canary + tickers_g4 + tickers_g12 + tickers_safe))

data = get_adj_close_data(tickers_all)  # 모든 데이터
rebal_data = get_rebalance_date(data)  # 월말 데이터
#print(rebal_data)

# aggressive strategy
baa_g4 = pd.DataFrame(columns=tickers_all)
res = []    # 총 자산 시작은 100

canary_data = rebal_data[tickers_canary]
profit = rebal_data.pct_change()    # 수익률 = (매도가격 - 매수가격) / 매수가격
n=12

for i in range(n, rebal_data.shape[0]):

    # 1-3-6-12 weight 구하기
    m1 = (canary_data.iloc[i]-canary_data.iloc[i-1])/canary_data.iloc[i-1]   # 1개월
    m3 = (canary_data.iloc[i]-canary_data.iloc[i-3])/canary_data.iloc[i-3]   # 3개월
    m6 = (canary_data.iloc[i]-canary_data.iloc[i-6])/canary_data.iloc[i-6]   # 6개월
    m12 = (canary_data.iloc[i]-canary_data.iloc[i-12])/canary_data.iloc[i-12]   # 12개월
    momentum_score = m1*12 + m3*4 + m6*2 + m12*1

    buy = dict()
    if min(momentum_score) <= 0:     # 안전자산
        safe = rebal_data[tickers_safe].iloc[i] / rebal_data[tickers_safe].iloc[i-n:i].mean()
        safe_top3 = safe.nlargest(3)
        for j in range(3):
            try:
                if safe_top3[j] > safe["BIL"]:
                    name = safe_top3.index[j]
                else:
                    name = "BIL"
                buy[name] += (1/3)*100
            except:
                buy[name] = (1/3)*100
        print("safe : ", buy)

    else:
        # 공격형(g4)
        aggresive = rebal_data[tickers_g4].iloc[i] / rebal_data[tickers_g4].iloc[i-n:i].mean()
        agg_top1 = aggresive.nlargest(1)
        buy[agg_top1.index[0]] = 100
        print("G4 : ", buy)

    # if series(단일 결과 출력)
    if i == n:
        one = pd.DataFrame([list(buy.values())], columns=list(buy.keys()), index = [rebal_data.index[i]])
        baa_g4 = pd.concat([baa_g4, one])
        res.append(100)

    # if not series(more than 2 days)
    else:
        total = sum(((1+profit.iloc[i])*baa_g4.iloc[-1]).fillna(0))
        res.append(total)
        one = pd.DataFrame([list(buy.values())], columns=list(buy.keys()), index=[rebal_data.index[i]]) * total / 100
        baa_g4 = pd.concat([baa_g4, one])

    baa_g4["Total"] = res
    baa_g4.tail()

qs.reports.html(baa_g4["Total"], output='./file-name.html')





