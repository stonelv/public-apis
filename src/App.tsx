import { useState, useEffect } from 'react'
import './App.css'

// API 数据类型定义
interface API {
  name: string
  description: string
  link: string
}

interface Category {
  category: string
  apis: API[]
}

interface APIData {
  categories: Category[]
}

function App() {
  // 状态管理
  const [apis, setApis] = useState<API[]>([])
  const [filteredApis, setFilteredApis] = useState<API[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [favorites, setFavorites] = useState<Set<string>>(new Set())

  // 加载本地 API 数据
  useEffect(() => {
    fetch('/data/apis.json')
      .then(response => response.json())
      .then((data: APIData) => {
        // 扁平化数据结构
        const allApis: API[] = []
        data.categories.forEach(category => {
          allApis.push(...category.apis)
        })
        setApis(allApis)
        setFilteredApis(allApis)
      })
      .catch(error => console.error('Error loading API data:', error))
  }, [])

  // 加载收藏数据
  useEffect(() => {
    const savedFavorites = localStorage.getItem('apiFavorites')
    if (savedFavorites) {
      try {
        const favoriteSet = new Set(JSON.parse(savedFavorites))
        setFavorites(favoriteSet)
      } catch (error) {
        console.error('Error parsing favorites:', error)
      }
    }
  }, [])

  // 保存收藏数据
  useEffect(() => {
    localStorage.setItem('apiFavorites', JSON.stringify(Array.from(favorites)))
  }, [favorites])

  // 搜索功能
  useEffect(() => {
    if (!searchTerm) {
      setFilteredApis(apis)
      return
    }

    const filtered = apis.filter(api => 
      api.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      api.description.toLowerCase().includes(searchTerm.toLowerCase())
    )
    setFilteredApis(filtered)
  }, [searchTerm, apis])

  // 切换收藏状态
  const toggleFavorite = (apiName: string) => {
    const newFavorites = new Set(favorites)
    if (newFavorites.has(apiName)) {
      newFavorites.delete(apiName)
    } else {
      newFavorites.add(apiName)
    }
    setFavorites(newFavorites)
  }

  return (
    <div className="app">
      <header className="header">
        <h1>API 目录</h1>
        <div className="search-container">
          <input
            type="text"
            placeholder="搜索 API (名称或描述)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <span className="search-count">
            {filteredApis.length} 个结果
          </span>
        </div>
      </header>

      <main className="main">
        {filteredApis.length > 0 ? (
          <div className="api-list">
            {filteredApis.map((api, index) => (
              <div key={index} className="api-card">
                <div className="api-header">
                  <h3 className="api-name">{api.name}</h3>
                  <button
                    className={`favorite-button ${favorites.has(api.name) ? 'favorited' : ''}`}
                    onClick={() => toggleFavorite(api.name)}
                    title={favorites.has(api.name) ? '取消收藏' : '收藏'}
                  >
                    {favorites.has(api.name) ? '★' : '☆'}
                  </button>
                </div>
                <p className="api-description">{api.description}</p>
                <a
                  href={api.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="api-link"
                >
                  访问 API
                </a>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-results">
            <p>没有找到匹配的 API</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
