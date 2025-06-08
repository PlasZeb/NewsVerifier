import pandas as pd
import os

# Load datasets
fake_df = pd.read_csv("Fake.csv")
true_df = pd.read_csv("True.csv")

# Add labels
fake_df["label"] = 0 
true_df["label"] = 1 

# Combine
combined_df = pd.concat([fake_df, true_df], ignore_index=True)

# Only keep imp cols
combined_df = combined_df[["title", "text", "label"]]
combined_df["text"] = combined_df["title"].fillna('') + " " + combined_df["text"].fillna('')
combined_df = combined_df[["text", "label"]]

# Save CSV
os.makedirs("data", exist_ok=True)
combined_df.to_csv("fake_news_dataset.csv", index=False)
print("Successfull")
