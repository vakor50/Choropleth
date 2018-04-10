import json
import pandas as pd 
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import math, nltk, warnings
from nltk.corpus import wordnet
from sklearn import linear_model
from sklearn.neighbors import NearestNeighbors
from fuzzywuzzy import fuzz
# from wordcloud import WordCloud, STOPWORDS

def load_tmdb_movies(path):
	df = pd.read_csv(path)
	# convert string to date
	df['release_date'] = pd.to_datetime(df['release_date']).apply(lambda x: x.date())
	# designate columns to be read
	json_columns = ['genres', 'keywords', 'production_countries', 'production_companies', 'spoken_languages']
	for column in json_columns:
		df[column] = df[column].apply(json.loads)
	return df 

def load_tmdb_credits(path):
	df = pd.read_csv(path)
	# designate columns to be read
	json_columns = ['cast', 'crew']
	for column in json_columns:
		df[column] = df[column].apply(json.loads)
	return df

LOST_COLUMNS = [
    'actor_1_facebook_likes',
    'actor_2_facebook_likes',
    'actor_3_facebook_likes',
    'aspect_ratio',
    'cast_total_facebook_likes',
    'color',
    'content_rating',
    'director_facebook_likes',
    'facenumber_in_poster',
    'movie_facebook_likes',
    'movie_imdb_link',
    'num_critic_for_reviews',
    'num_user_for_reviews'
    ]

TMDB_TO_IMDB_SIMPLE_EQUIVALENCIES = {
    'budget': 'budget',
    'genres': 'genres',
    'revenue': 'gross',
    'title': 'movie_title',
    'runtime': 'duration',
    'original_language': 'language',  # it's possible that spoken_languages would be a better match
    'keywords': 'plot_keywords',
    'vote_count': 'num_voted_users',
    }

IMDB_COLUMNS_TO_REMAP = {'imdb_score': 'vote_average'}

def safe_access(container, index_values):
    # return missing value rather than an error upon indexing/key failure
    result = container
    try:
        for idx in index_values:
            result = result[idx]
        return result
    except IndexError or KeyError:
        return pd.np.nan

def get_director(crew_data):
    directors = [x['name'] for x in crew_data if x['job'] == 'Director']
    return safe_access(directors, [0])

def pipe_flatten_names(keywords):
    return '|'.join([x['name'] for x in keywords])

def convert_to_original_format(movies, credits):
    tmdb_movies = movies.copy()
    tmdb_movies.rename(columns=TMDB_TO_IMDB_SIMPLE_EQUIVALENCIES, inplace=True)
    tmdb_movies['title_year'] = pd.to_datetime(tmdb_movies['release_date']).apply(lambda x: x.year)
    # I'm assuming that the first production country is equivalent, but have not been able to validate this
    tmdb_movies['country'] = tmdb_movies['production_countries'].apply(lambda x: safe_access(x, [0, 'name']))
    tmdb_movies['language'] = tmdb_movies['spoken_languages'].apply(lambda x: safe_access(x, [0, 'name']))
    tmdb_movies['director_name'] = credits['crew'].apply(get_director)
    tmdb_movies['actor_1_name'] = credits['cast'].apply(lambda x: safe_access(x, [1, 'name']))
    tmdb_movies['actor_2_name'] = credits['cast'].apply(lambda x: safe_access(x, [2, 'name']))
    tmdb_movies['actor_3_name'] = credits['cast'].apply(lambda x: safe_access(x, [3, 'name']))
    tmdb_movies['genres'] = tmdb_movies['genres'].apply(pipe_flatten_names)
    tmdb_movies['plot_keywords'] = tmdb_movies['plot_keywords'].apply(pipe_flatten_names)
    return tmdb_movies

def count_word(df, ref_col, liste):
    keyword_count = dict()
    for s in liste: keyword_count[s] = 0
    for liste_keywords in df[ref_col].str.split('|'):
        if type(liste_keywords) == float and pd.isnull(liste_keywords): continue
        #for s in liste:
        for s in [s for s in liste_keywords if s in liste]:
            if pd.notnull(s): keyword_count[s] += 1
    #______________________________________________________________________
    # convert the dictionary in a list to sort the keywords by frequency
    keyword_occurences = []
    for k,v in keyword_count.items():
        keyword_occurences.append([k,v])
    keyword_occurences.sort(key = lambda x:x[1], reverse = True)
    return keyword_occurences, keyword_count

plt.rcParams["patch.force_edgecolor"] = True
plt.style.use('fivethirtyeight')
mpl.rc('patch', edgecolor = 'dimgray', linewidth=1)
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "last_expr"
pd.options.display.max_columns = 50
# %matplotlib inline
warnings.filterwarnings('ignore')
PS = nltk.stem.PorterStemmer()
#__________________
# load the dataset
#df_initial = pd.read_csv("../data/movies/movie_metadata.csv")
credits = load_tmdb_credits("data/movies/tmdb_5000_credits.csv")
movies = load_tmdb_movies("data/movies/tmdb_5000_movies.csv")
df_initial = convert_to_original_format(movies, credits)
print('Shape:',df_initial.shape)
#__________________________________________
# info on variable types and filling factor
# tab_info=pd.DataFrame(df_initial.dtypes).T.rename(index={0:'column type'})
# tab_info=tab_info.append(pd.DataFrame(df_initial.isnull().sum()).T.rename(index={0:'null values'}))
# tab_info=tab_info.append(pd.DataFrame(df_initial.isnull().sum()/df_initial.shape[0]*100).T.
#                          rename(index={0:'null values (%)'}))
# tab_info

# list the keywords which are in the dataset:
set_keywords = set()
for liste_keywords in df_initial['plot_keywords'].str.split('|').values:
    if isinstance(liste_keywords, float): continue  # only happen if liste_keywords = NaN
    set_keywords = set_keywords.union(liste_keywords)

# gives access to a list of keywords which are sorted by decreasing frequency:
keyword_occurences, dum = count_word(df_initial, 'plot_keywords', set_keywords)
# drop entries with no keywords to prevent a null error in the next plot.
keyword_occurences = [x for x in keyword_occurences if x[0]]
print(keyword_occurences[:5])

# I define the dictionary used to produce the wordcloud
words = dict()
trunc_occurences = keyword_occurences[0:50]
for s in trunc_occurences:
    words[s[0]] = s[1]

# determine the amount of data which is missing in every variable:
missing_df = df_initial.isnull().sum(axis=0).reset_index()
missing_df.columns = ['column_name', 'missing_count']
missing_df['filling_factor'] = (df_initial.shape[0] 
                                - missing_df['missing_count']) / df_initial.shape[0] * 100
missing_df.sort_values('filling_factor').reset_index(drop = True)

# Number of films per year
df_initial['decade'] = df_initial['title_year'].apply(lambda x:((x-1900)//10)*10)
#__________________________________________________________________
# function that extract statistical parameters from a grouby objet:
def get_stats(gr):
    return {'min':gr.min(),'max':gr.max(),'count': gr.count(),'mean':gr.mean()}
#______________________________________________________________
# Creation of a dataframe with statitical infos on each decade:
test = df_initial['title_year'].groupby(df_initial['decade']).apply(get_stats).unstack()
# print(test)

# Genres
genre_labels = set()
for s in df_initial['genres'].str.split('|').values:
    genre_labels = genre_labels.union(set(s))

keyword_occurences, dum = count_word(df_initial, 'genres', genre_labels)
keyword_occurences = [x for x in keyword_occurences if x[0]]
keyword_occurences[:5]
# print(keyword_occurences[:5])

# checking for the existence of duplicated entries

#doubled_entries = df_initial[df_initial.duplicated()]
doubled_entries = df_initial[df_initial.id.duplicated()]
doubled_entries.shape

#df_temp = df_initial.drop_duplicates()
df_temp = df_initial

# examine the rows with entries only duplicated according to the movie_title, title_year, and director_name variables:
list_var_duplicates = ['movie_title', 'title_year', 'director_name']
# list of the entries with identical titles:
liste_duplicates = df_temp['movie_title'].map(df_temp['movie_title'].value_counts() > 1)
print("Nb. of duplicate entries: {}".format(
    len(df_temp[liste_duplicates][list_var_duplicates])))
# examine in a few cases the variables for which the entries differ.
# df_temp[liste_duplicates][list_var_duplicates].sort_values('movie_title')[31:41]
df_temp[liste_duplicates][list_var_duplicates].sort_values('movie_title')

















# https://www.kaggle.com/sohier/film-recommendation-engine-converted-to-use-tmdb