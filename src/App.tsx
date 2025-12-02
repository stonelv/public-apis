import { useState, useEffect } from 'react'
import { API, FavoriteState } from './types'
import apisData from '../data/apis.json'

function App() {
  // 搜索关键词状态
  const [searchTerm, setSearchTerm] = useState('')
  // 收藏状态，存储在 localStorage 中
  const [favorites, setFavorites] = useState<FavoriteState>({});

  // 初始化时从 localStorage 加载收藏数据
  useEffect(() => {
    const savedFavorites = localStorage.getItem('apiFavorites');
    if (savedFavorites) {
      setFavorites(JSON.parse(savedFavorites));
    }
  }, []);

  // 收藏状态变化时保存到 localStorage
  useEffect(() => {
    localStorage.setItem('apiFavorites', JSON.stringify(favorites));
  }, [favorites]);

  // 切换收藏状态
  const toggleFavorite = (apiName: string) => {
    setFavorites(prev => ({
      ...prev,
      [apiName]: !prev[apiName]
    }));
  };

  // 根据搜索关键词过滤 API 列表
  const filteredApis = apisData.filter((api: API) => {
    const lowerTerm = searchTerm.toLowerCase();
    return (
      api.name.toLowerCase().includes(lowerTerm) ||
      (api.description || '').toLowerCase().includes(lowerTerm)
    );
  });

  return (
    <div className="app">
      <header>
        <h1>Public APIs</h1>
        <p>Discover free public APIs for your projects</p>
      </header>

      <div className="search-container">
        <input
          type="text"
          className="search-input"
          placeholder="Search APIs by name or description..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {filteredApis.length > 0 ? (
        <div className="apis-grid">
          {filteredApis.map((api) => (
            <div key={api.link} className="api-card">
              <div className="api-header">
                <h3 className="api-name">{api.name}</h3>
                <button
                  className={`favorite-btn ${favorites[api.name] ? 'active' : ''}`}
                  onClick={() => toggleFavorite(api.name)}
                  aria-label={favorites[api.name] ? 'Remove from favorites' : 'Add to favorites'}
                >
                  {favorites[api.name] ? '⭐' : '☆'}
                </button>
              </div>
              <p className="api-description">{api.description}</p>
              <a
                href={api.link}
                className="api-link"
                target="_blank"
                rel="noopener noreferrer"
              >
                Visit Website →
              </a>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <h3>No APIs found</h3>
          <p>Try adjusting your search terms</p>
        </div>
      )}
    </div>
  );
}

export default App;
