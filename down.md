
name: Run Down Clues Script Daily

on:
  schedule:
    - cron: '0 5 * * *'  # 10:30 AM IST (UTC+5:30)
  workflow_dispatch:  # allows manual trigger too

jobs:
  post-down:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run Down Clues Script
      env:
        BLOGGER_API_TOKEN: ${{ secrets.BLOGGER_API_TOKEN }}
        BLOG_ID: ${{ secrets.BLOG_ID }}
      run: |
        python down.py
