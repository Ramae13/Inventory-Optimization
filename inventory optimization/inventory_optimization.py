# -*- coding: utf-8 -*-
"""Inventory Optimization

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1YtaToFcoxOoiJhqRVBuqhGwpwUYfeoOt
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import datetime

df = pd.read_csv('retail_store_inventory.csv')

print(df.head())

print("\nMissing values in each column:")
print(df.isnull().sum())

df.fillna(method='ffill', inplace=True)

df['Date'] = pd.to_datetime(df['Date'])

label_encoder = LabelEncoder()
df['Store ID'] = label_encoder.fit_transform(df['Store ID'])
df['Product ID'] = label_encoder.fit_transform(df['Product ID'])
df['Category'] = label_encoder.fit_transform(df['Category'])
df['Region'] = label_encoder.fit_transform(df['Region'])
df['Weather Condition'] = label_encoder.fit_transform(df['Weather Condition'])
df['Holiday/Promotion'] = df['Holiday/Promotion'].astype(int)

print(df.info())

plt.figure(figsize=(10, 6))
df.groupby('Date')['Units Sold'].sum().plot()
plt.title("Total Units Sold Over Time")
plt.xlabel("Date")
plt.ylabel("Units Sold")
plt.show()

plt.figure(figsize=(10, 6))
sns.boxplot(x='Category', y='Units Sold', data=df)
plt.title("Units Sold by Product Category")
plt.show()

plt.figure(figsize=(10, 6))
sns.boxplot(x='Weather Condition', y='Units Sold', data=df)
plt.title("Impact of Weather on Units Sold")
plt.show()

plt.figure(figsize=(10, 6))
sns.heatmap(df[['Inventory Level', 'Units Sold']].corr(), annot=True, cmap='coolwarm')
plt.title("Correlation between Inventory Level and Units Sold")
plt.show()

from sklearn.preprocessing import MinMaxScaler

store_data = df[(df['Store ID'] == 0) & (df['Product ID'] == 0)]

store_data.set_index('Date', inplace=True)

store_data = store_data[['Units Sold', 'Inventory Level']]

scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(store_data)

def create_sequences(data, seq_length):
    x = []
    y = []
    for i in range(len(data) - seq_length):
        x.append(data[i:i + seq_length])
        y.append(data[i + seq_length, 0])  # Predicting 'Units Sold'
    return np.array(x), np.array(y)

SEQ_LENGTH = 30
x, y = create_sequences(scaled_data, SEQ_LENGTH)

train_size = int(len(x) * 0.8)
x_train, x_test = x[:train_size], x[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout

model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(SEQ_LENGTH, x_train.shape[2])))
model.add(Dropout(0.2))
model.add(LSTM(units=50, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(units=1))  # Output layer predicting Units Sold

model.compile(optimizer='adam', loss='mean_squared_error')

history = model.fit(x_train, y_train, epochs=10, batch_size=32, validation_data=(x_test, y_test))

predictions = model.predict(x_test)

predictions = scaler.inverse_transform(np.concatenate((predictions, np.zeros((predictions.shape[0], scaled_data.shape[1] - 1))), axis=1))[:, 0]

plt.figure(figsize=(10, 6))
plt.plot(store_data.index[-len(y_test):], scaler.inverse_transform(np.concatenate((y_test.reshape(-1, 1), np.zeros((len(y_test), scaled_data.shape[1] - 1))), axis=1))[:, 0], label='Actual')
plt.plot(store_data.index[-len(y_test):], predictions, label='Predicted')
plt.title('Demand Forecasting (LSTM)')
plt.legend()
plt.show()

lead_time = 7
average_demand = np.mean(predictions)  # Using predicted demand as average demand
reorder_point = average_demand * lead_time

order_cost = 50
holding_cost = 5  # Example holding cost per unit per day
EOQ = np.sqrt((2 * average_demand * order_cost) / holding_cost)

print(f"Reorder Point (ROP): {reorder_point} units")
print(f"Economic Order Quantity (EOQ): {EOQ} units")

df['Price'] = df['Price']  # Assuming price data exists
df['Price Elasticity'] = df['Units Sold'].pct_change() / df['Price'].pct_change()

# Visualize the relationship
plt.figure(figsize=(10, 6))
sns.scatterplot(x='Price', y='Price Elasticity', data=df)
plt.title("Price vs Price Elasticity")
plt.show()
