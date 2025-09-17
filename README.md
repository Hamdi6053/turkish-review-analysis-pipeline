# Customer Feedback Analysis Pipeline

This project is an end-to-end data science solution that scrapes Turkish customer reviews from various online platforms (Google Play, Şikayetvar, Ekşi Sözlük), processes them with AI-powered tools, classifies them into categories, and performs sentiment analysis.

## Project Objective

The goal of this project is to automatically extract valuable insights from customer feedback, identify general trends about a brand or product, and eliminate manual workload by automating the entire process.

## Core Features

- **Multi-Channel Data Scraping**: Scrapes data from platforms like Google Play, Şikayetvar, and Ekşi Sözlük using `Selenium` and `Requests/BS4`.
- **LLM-Powered Data Labeling**: Automatically labels large datasets into predefined categories (e.g., "Delivery", "Product Quality") using local language models (LLMs) like `Ollama` and `Gemma2`.
- **Ensemble Model Training**: Trains an ensemble model (Voting Classifier) for each category, combining over 10 different classifiers based on `Scikit-learn`.
- **Multi-Category Prediction**: Predicts which categories new, unlabeled comments belong to using the trained models.
- **Sentiment Analysis with Deep Learning**: Analyzes the sentiment scores (positive/negative) of categorized comments using `Hugging Face Transformers` and a BERT model pre-trained for the Turkish language (`savasy/bert-base-turkish-sentiment-cased`).
- **Modular and Extensible Architecture**: The project consists of modular scripts, each focused on a specific task (`scraping`, `labeling`, `ml`, `analysis`).

## Project Structure

```
.
├── Web Scraping/
│   └── scrapers/
│       ├── google_play_scraper.py
│       ├── sikayetvar_scraper.py
│       └── eksisozluk_scraper.py
├── data/
│   ├── filter_short_comments.py
│   └── merge_category_excels.py
├── labeling/
│   └── category_labeling_llm.py
├── ml/
│   ├── model_training_ensemble.py
│   ├── model_trainer.py
│   └── category_prediction.py
├── analysis/
│   └── bert_sentiment_tr.py
└── requirements.txt
```

- **`Web Scraping/scrapers/`**: Contains the data scraping scripts.
- **`data/`**: Includes scripts for data preprocessing steps (filtering, merging).
- **`labeling/`**: Used for labeling comments with an LLM.
- **`ml/`**: Where machine learning models are trained and predictions are made.
- **`analysis/`**: Performs sentiment analysis on the prediction results.

## Setup and Usage

### 1. Install Dependencies

Before running the project, install the required libraries from the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 2. Step-by-Step Workflow

#### Step 1: Data Collection (Scraping)
Collect comments by running the relevant scraper script. For example:
```bash
python "Web Scraping/scrapers/google_play_scraper.py"
```

#### Step 2: Data Preprocessing
Filter or merge the collected data.
```bash
python "data/filter_short_comments.py"
```

#### Step 3: Data Labeling with LLM
To create a training dataset, run the `category_labeling_llm.py` script. This requires `Ollama` to be running in the background. The script will interactively ask which category you want to process and how many samples to label.
```bash
python "labeling/category_labeling_llm.py"
```
The output of this step will be separate Excel files for each category, saved in the `kategori_sonuclari/` folder.

#### Step 4: Model Training
Train the classification models for each category using the labeled Excel files.
```bash

python "ml/model_training_ensemble.py"


python "ml/model_trainer.py"
```
This script will generate `model_{category_name}.pkl` files in the project's root directory for each category.

#### Step 5: Category Prediction on New Data
Classify a new, unlabeled dataset using the trained models.
```bash
python "ml/category_prediction.py"
```
This script will produce an output file named `tahmin_sonuclari.xlsx`.

#### Step 6: Sentiment Analysis
Perform sentiment analysis on the categorized comments.
```bash
python "analysis/bert_sentiment_tr.py"
```
This script reads the `tahmin_sonuclari.xlsx` file and creates the final output, `duygu_analizi_sonuclari.xlsx`.

## Technologies Used

- **Programming Language**: Python 3
- **Data Processing**: Pandas, NumPy
- **Web Scraping**: Selenium, BeautifulSoup4, Requests
- **Machine Learning**: Scikit-learn, Imbalanced-learn
- **Deep Learning**: PyTorch, Hugging Face Transformers
- **LLM Integration**: Ollama
- **Utility Libraries**: TQDM, Colorama, Joblib
