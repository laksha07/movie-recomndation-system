import streamlit as st
import pickle
import requests
from concurrent.futures import ThreadPoolExecutor

# --- PAGE CONFIG ---
st.set_page_config(page_title="Movie Recommender", layout="wide")

# --- 1. CACHING API CALLS ---
# This ensures that if you select the same movie twice, it loads instantly from memory
@st.cache_data
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=c7ec19ffdd3279641fb606d19ceb9bb1&language=en-US"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
    except Exception:
        pass
    return "https://via.placeholder.com/500x750?text=No+Poster"

# --- 2. PARALLEL FETCHING ---
# This pulls all posters at once instead of one-by-one
def fetch_all_posters(movie_ids):
    with ThreadPoolExecutor() as executor:
        posters = list(executor.map(fetch_poster, movie_ids))
    return posters

# --- DATA LOADING ---
@st.cache_resource # Cache the heavy pickle files so they only load once
def load_data():
    movies = pickle.load(open("movies_list.pkl", 'rb'))
    similarity = pickle.load(open("similarity.pkl", 'rb'))
    return movies, similarity

movies, similarity = load_data()
movies_list = movies['title'].values

# --- UI ---
st.markdown("<h1 style='text-align: center; color: #E50914;'>🎬 MOVIE RECOMMENDERS</h1>", unsafe_allow_html=True)

# Trending Carousel (using parallel fetch)
carousel_ids = [1632, 299536, 17455, 2830, 429422]
if 'carousel_urls' not in st.session_state:
    st.session_state.carousel_urls = fetch_all_posters(carousel_ids)

cols = st.columns(5)
for col, url in zip(cols, st.session_state.carousel_urls):
    col.image(url, use_container_width=True)

st.divider()

# Selection
selectvalue = st.selectbox("Select a movie you liked:", movies_list)

def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    
    rec_names = []
    rec_ids = []
    for i in distances[1:6]:
        rec_names.append(movies.iloc[i[0]].title)
        rec_ids.append(movies.iloc[i[0]].id)
    
    # Speed up: Fetch all posters in parallel
    rec_posters = fetch_all_posters(rec_ids)
    return rec_names, rec_posters

if st.button("Show Recommendations"):
    with st.spinner('Fetching recommendations...'):
        names, posters = recommend(selectvalue)
        
        cols = st.columns(5)
        for i in range(5):
            with cols[i]:
                st.text(names[i])
                st.image(posters[i], use_container_width=True)