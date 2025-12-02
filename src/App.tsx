import { useState, useEffect } from 'react';
import './App.css';

// 定义 API 数据类型
interface Api {
  name: string;
  description: string;
  link: string;
}

function App() {
  // 状态管理
  const [apis, setApis] = useState<Api[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [favorites, setFavorites] = useState<Api[]>([]);

  // 加载本地 API 数据
  useEffect(() => {
    fetch('/data/apis.json')
      .then((response) => response.json())
      .then((data) => setApis(data))
      .catch((error) => console.error('Error loading APIs:', error));
  }, []);

  // 从 localStorage 加载收藏
  useEffect(() => {
    const savedFavorites = localStorage.getItem('favorites');
    if (savedFavorites) {
      setFavorites(JSON.parse(savedFavorites));
    }
  }, []);

  // 保存收藏到 localStorage
  useEffect(() => {
    localStorage.setItem('favorites', JSON.stringify(favorites));
  }, [favorites]);

  // 搜索功能
  const filteredApis = apis.filter((api) =>
    api.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (api.description || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  // 切换收藏状态
  const toggleFavorite = (api: Api) => {
    setFavorites((prevFavorites) => {
      const isFavorite = prevFavorites.some((fav) => fav.link === api.link);
      if (isFavorite) {
        return prevFavorites.filter((fav) => fav.link !== api.link);
      } else {
        return [...prevFavorites, api];
      }
    });
  };

  // 检查是否为收藏
  const isFavorite = (api: Api) => {
    return favorites.some((fav) => fav.link === api.link);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Public APIs</h1>
        <input
          type="text"
          placeholder="Search APIs by name or description..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </header>
      <main className="App-main">
        <div className="apis-container">
          {filteredApis.map((api) => (
            <div key={api.link} className="api-card">
              <div className="api-header">
                <h2 className="api-name">{api.name}</h2>
                <button
                  className={`favorite-button ${isFavorite(api) ? 'favorited' : ''}`}
                  onClick={() => toggleFavorite(api)}
                  aria-label={isFavorite(api) ? 'Remove from favorites' : 'Add to favorites'}
                >
                  {isFavorite(api) ? '★' : '☆'}
                </button>
              </div>
              <p className="api-description">{api.description}</p>
              <a
                href={api.link}
                target="_blank"
                rel="noopener noreferrer"
                className="api-link"
              >
                Visit API
              </a>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

export default App;