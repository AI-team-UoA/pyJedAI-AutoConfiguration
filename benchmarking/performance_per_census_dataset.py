import os
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

census_datasets = ['10K','50K','100K','200K','300K','1M','2M']
# census_datasets = ['10K','50K']

TOPK = 20

#  create results csv

summary_df = pd.DataFrame(columns=['dataset', 'predicted', 'max'])

for census_results in census_datasets:

    #  if file exists
    if not os.path.isfile("./predictions/" + census_results + "_results.csv"):
        print("File not found: ", census_results)
        continue

    results = pd.read_csv("./predictions/" + census_results + "_results.csv")

    true = results['true']
    predicted = results['predicted']

    print("\n\nPerformance on Test Set: ", census_results)
    MSE = mean_squared_error(true, predicted)
    print("Mean Squared Error:", MSE)


    topKpredicted = results.sort_values(by='predicted', ascending=False).head(TOPK)
    topKtrue = results.sort_values(by='true', ascending=False).head(TOPK)

    print("\n\nTop K (Sorted on Predicted): ")
    print(topKpredicted)

    print("\nTop K (Sorted on True)")
    print(topKtrue)

    LOCAL_BEST_TRUE = topKtrue['true'].max()
    print("\n\nLocal Best True: ", LOCAL_BEST_TRUE)

    BEST_PREDICTED = topKpredicted['predicted'].idxmax()

    print(topKpredicted.loc[BEST_PREDICTED,:])
    BEST_PREDICTED = topKpredicted.loc[BEST_PREDICTED, 'true']

    print("\n\nBest Predicted: ", BEST_PREDICTED)

    new_row = pd.DataFrame([{'dataset': census_results, 'predicted': BEST_PREDICTED, 'max': LOCAL_BEST_TRUE}])
    summary_df = pd.concat([summary_df, new_row], ignore_index=True)

summary_df.to_csv('./predictions/summary.csv', index=False)