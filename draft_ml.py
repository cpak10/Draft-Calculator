import pandas as pd
import tensorflow as tf
import numpy
from tensorflow import feature_column
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split

# creating a machine learning model that will look at the drafts from the matches from the top regions
# loading the data from the API 
df = pd.read_excel('Challenger Patch 10.18 NA.xlsx')
df1 = pd.read_excel('Challenger Patch 10.18 EU.xlsx')
df2 = pd.read_excel('Challenger Patch 10.18 KR.xlsx')
df = df.append(df1)
df = df.append(df2)
print(df)
# preparing the data for implementation into the neural net
row, col = df.shape
df = df[df.columns[-6:]]
df = df[['result', 'top', 'jng', 'mid']]
train_file = df.head(int(row * .75))
test_file = df.tail(int(row * .25))
train_result = train_file.pop('result')
test_result = test_file.pop('result')
tf.random.set_seed(10)
# creating the layers of the model
model = tf.keras.Sequential([
    layers.Embedding(df.max().iloc[1] + 1, 16),
    layers.GlobalAveragePooling1D(),
    # layers.Dense(128, activation='relu'),
    layers.Dense(16, activation='relu'),
    layers.Dense(1, activation='sigmoid')
])
model.compile(
    optimizer='adam',
    loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
    metrics=['accuracy']
)
model.fit(
    train_file, train_result,
    epochs=100
)
# testing the data
loss, accuracy = model.evaluate(test_file, test_result)
print("Accuracy", accuracy)