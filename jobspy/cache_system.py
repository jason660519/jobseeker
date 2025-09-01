"""智能快取系統

此模組提供多層次的快取機制，包括記憶體快取、檔案快取和 Redis 快取。
"""

from __future__ import annotations

import json
import hashlib
import pickle
import time
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from jobspy.model import JobResponse, JobPost, Site
from jobspy.enhanced_logging import get_enhanced_logger, LogCategory


class CacheType(Enum):
    """快取類型枚舉"""
    MEMORY = "memory"
    FILE = "file"
    REDIS = "redis"
    HYBRID = "hybrid"


class CacheStrategy(Enum):
    """快取策略枚舉"""
    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最少使用頻率
    TTL = "ttl"  # 基於時間過期
    FIFO = "fifo"  # 先進先出


@dataclass
class CacheEntry:
    """快取條目"""
    key: str
    data: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def is_expired(self) -> bool:
        """檢查是否過期"""
        if self.ttl_seconds is None:
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def update_access(self):
        """更新存取資訊"""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'key': self.key,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'ttl_seconds': self.ttl_seconds,
            'metadata': self.metadata
        }


class CacheStats:
    """快取統計"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_requests = 0
        self.total_size = 0
        self._lock = threading.Lock()
    
    def record_hit(self):
        """記錄快取命中"""
        with self._lock:
            self.hits += 1
            self.total_requests += 1
    
    def record_miss(self):
        """記錄快取未命中"""
        with self._lock:
            self.misses += 1
            self.total_requests += 1
    
    def record_eviction(self):
        """記錄快取驅逐"""
        with self._lock:
            self.evictions += 1
    
    def update_size(self, size: int):
        """更新快取大小"""
        with self._lock:
            self.total_size = size
    
    def get_hit_rate(self) -> float:
        """獲取命中率"""
        with self._lock:
            if self.total_requests == 0:
                return 0.0
            return self.hits / self.total_requests * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計資訊"""
        with self._lock:
            return {
                'hits': self.hits,
                'misses': self.misses,
                'evictions': self.evictions,
                'total_requests': self.total_requests,
                'hit_rate': self.get_hit_rate(),
                'total_size': self.total_size
            }
    
    def reset(self):
        """重置統計"""
        with self._lock:
            self.hits = 0
            self.misses = 0
            self.evictions = 0
            self.total_requests = 0
            self.total_size = 0


class BaseCache(ABC):
    """快取基類"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.stats = CacheStats()
        self.logger = get_enhanced_logger("cache")
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """獲取快取值"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """設置快取值"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """刪除快取值"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """清空快取"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """獲取快取大小"""
        pass
    
    def generate_key(self, *args, **kwargs) -> str:
        """生成快取鍵"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode()).hexdigest()


class MemoryCache(BaseCache):
    """記憶體快取實現"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600, 
                 strategy: CacheStrategy = CacheStrategy.LRU):
        super().__init__(max_size, default_ttl)
        self.strategy = strategy
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """獲取快取值"""
        with self._lock:
            if key not in self._cache:
                self.stats.record_miss()
                self.logger.debug(f"快取未命中: {key}", category=LogCategory.CACHE)
                return None
            
            entry = self._cache[key]
            
            # 檢查是否過期
            if entry.is_expired():
                del self._cache[key]
                self.stats.record_miss()
                self.logger.debug(f"快取過期: {key}", category=LogCategory.CACHE)
                return None
            
            # 更新存取資訊
            entry.update_access()
            self.stats.record_hit()
            self.logger.debug(f"快取命中: {key}", category=LogCategory.CACHE)
            return entry.data
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """設置快取值"""
        with self._lock:
            try:
                # 檢查是否需要驅逐
                if len(self._cache) >= self.max_size and key not in self._cache:
                    self._evict_one()
                
                # 創建快取條目
                now = datetime.now()
                entry = CacheEntry(
                    key=key,
                    data=value,
                    created_at=now,
                    last_accessed=now,
                    access_count=0,
                    ttl_seconds=ttl or self.default_ttl
                )
                
                self._cache[key] = entry
                self.stats.update_size(len(self._cache))
                self.logger.debug(f"快取設置: {key}", category=LogCategory.CACHE)
                return True
                
            except Exception as e:
                self.logger.error(f"快取設置失敗: {key}, 錯誤: {str(e)}", category=LogCategory.CACHE)
                return False
    
    def delete(self, key: str) -> bool:
        """刪除快取值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self.stats.update_size(len(self._cache))
                self.logger.debug(f"快取刪除: {key}", category=LogCategory.CACHE)
                return True
            return False
    
    def clear(self) -> bool:
        """清空快取"""
        with self._lock:
            self._cache.clear()
            self.stats.update_size(0)
            self.logger.info("快取已清空", category=LogCategory.CACHE)
            return True
    
    def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        with self._lock:
            if key not in self._cache:
                return False
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                return False
            return True
    
    def size(self) -> int:
        """獲取快取大小"""
        with self._lock:
            return len(self._cache)
    
    def _evict_one(self):
        """驅逐一個快取條目"""
        if not self._cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # 最近最少使用
            key_to_evict = min(self._cache.keys(), 
                              key=lambda k: self._cache[k].last_accessed)
        elif self.strategy == CacheStrategy.LFU:
            # 最少使用頻率
            key_to_evict = min(self._cache.keys(), 
                              key=lambda k: self._cache[k].access_count)
        elif self.strategy == CacheStrategy.FIFO:
            # 先進先出
            key_to_evict = min(self._cache.keys(), 
                              key=lambda k: self._cache[k].created_at)
        else:
            # 預設使用 LRU
            key_to_evict = min(self._cache.keys(), 
                              key=lambda k: self._cache[k].last_accessed)
        
        del self._cache[key_to_evict]
        self.stats.record_eviction()
        self.logger.debug(f"快取驅逐: {key_to_evict}", category=LogCategory.CACHE)
    
    def cleanup_expired(self):
        """清理過期的快取條目"""
        with self._lock:
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self.stats.update_size(len(self._cache))
                self.logger.info(f"清理過期快取: {len(expired_keys)} 個條目", category=LogCategory.CACHE)


class FileCache(BaseCache):
    """檔案快取實現"""
    
    def __init__(self, cache_dir: str = "cache", max_size: int = 1000, 
                 default_ttl: int = 3600, use_json: bool = True):
        super().__init__(max_size, default_ttl)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.use_json = use_json
        self.index_file = self.cache_dir / "cache_index.json"
        self._index: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._load_index()
    
    def _load_index(self):
        """載入快取索引"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self._index = json.load(f)
        except Exception as e:
            self.logger.warning(f"載入快取索引失敗: {str(e)}", category=LogCategory.CACHE)
            self._index = {}
    
    def _save_index(self):
        """保存快取索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存快取索引失敗: {str(e)}", category=LogCategory.CACHE)
    
    def _get_file_path(self, key: str) -> Path:
        """獲取快取檔案路徑"""
        extension = '.json' if self.use_json else '.pkl'
        return self.cache_dir / f"{key}{extension}"
    
    def get(self, key: str) -> Optional[Any]:
        """獲取快取值"""
        with self._lock:
            if key not in self._index:
                self.stats.record_miss()
                return None
            
            entry_info = self._index[key]
            
            # 檢查是否過期
            if entry_info.get('ttl_seconds'):
                created_at = datetime.fromisoformat(entry_info['created_at'])
                if datetime.now() > created_at + timedelta(seconds=entry_info['ttl_seconds']):
                    self.delete(key)
                    self.stats.record_miss()
                    return None
            
            # 讀取檔案
            file_path = self._get_file_path(key)
            try:
                if self.use_json:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    with open(file_path, 'rb') as f:
                        data = pickle.load(f)
                
                # 更新存取資訊
                entry_info['last_accessed'] = datetime.now().isoformat()
                entry_info['access_count'] = entry_info.get('access_count', 0) + 1
                self._save_index()
                
                self.stats.record_hit()
                return data
                
            except Exception as e:
                self.logger.error(f"讀取快取檔案失敗: {key}, 錯誤: {str(e)}", category=LogCategory.CACHE)
                self.delete(key)
                self.stats.record_miss()
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """設置快取值"""
        with self._lock:
            try:
                # 檢查是否需要驅逐
                if len(self._index) >= self.max_size and key not in self._index:
                    self._evict_one()
                
                # 寫入檔案
                file_path = self._get_file_path(key)
                if self.use_json:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(value, f, ensure_ascii=False, indent=2, default=str)
                else:
                    with open(file_path, 'wb') as f:
                        pickle.dump(value, f)
                
                # 更新索引
                now = datetime.now()
                self._index[key] = {
                    'created_at': now.isoformat(),
                    'last_accessed': now.isoformat(),
                    'access_count': 0,
                    'ttl_seconds': ttl or self.default_ttl,
                    'file_path': str(file_path)
                }
                
                self._save_index()
                self.stats.update_size(len(self._index))
                return True
                
            except Exception as e:
                self.logger.error(f"設置快取失敗: {key}, 錯誤: {str(e)}", category=LogCategory.CACHE)
                return False
    
    def delete(self, key: str) -> bool:
        """刪除快取值"""
        with self._lock:
            if key in self._index:
                # 刪除檔案
                file_path = self._get_file_path(key)
                try:
                    if file_path.exists():
                        file_path.unlink()
                except Exception as e:
                    self.logger.warning(f"刪除快取檔案失敗: {key}, 錯誤: {str(e)}", category=LogCategory.CACHE)
                
                # 更新索引
                del self._index[key]
                self._save_index()
                self.stats.update_size(len(self._index))
                return True
            return False
    
    def clear(self) -> bool:
        """清空快取"""
        with self._lock:
            try:
                # 刪除所有快取檔案
                for key in list(self._index.keys()):
                    self.delete(key)
                
                self._index.clear()
                self._save_index()
                self.stats.update_size(0)
                return True
                
            except Exception as e:
                self.logger.error(f"清空快取失敗: {str(e)}", category=LogCategory.CACHE)
                return False
    
    def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        with self._lock:
            if key not in self._index:
                return False
            
            entry_info = self._index[key]
            
            # 檢查是否過期
            if entry_info.get('ttl_seconds'):
                created_at = datetime.fromisoformat(entry_info['created_at'])
                if datetime.now() > created_at + timedelta(seconds=entry_info['ttl_seconds']):
                    self.delete(key)
                    return False
            
            return True
    
    def size(self) -> int:
        """獲取快取大小"""
        with self._lock:
            return len(self._index)
    
    def _evict_one(self):
        """驅逐一個快取條目"""
        if not self._index:
            return
        
        # 使用 LRU 策略
        key_to_evict = min(self._index.keys(), 
                          key=lambda k: self._index[k]['last_accessed'])
        self.delete(key_to_evict)
        self.stats.record_eviction()


class RedisCache(BaseCache):
    """Redis 快取實現"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, 
                 db: int = 0, password: Optional[str] = None,
                 max_size: int = 10000, default_ttl: int = 3600,
                 key_prefix: str = 'jobspy:'):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis 不可用，請安裝 redis 套件")
        
        super().__init__(max_size, default_ttl)
        self.key_prefix = key_prefix
        self.redis_client = redis.Redis(
            host=host, port=port, db=db, password=password,
            decode_responses=True
        )
        
        # 測試連接
        try:
            self.redis_client.ping()
            self.logger.info("Redis 連接成功", category=LogCategory.CACHE)
        except Exception as e:
            self.logger.error(f"Redis 連接失敗: {str(e)}", category=LogCategory.CACHE)
            raise
    
    def _get_full_key(self, key: str) -> str:
        """獲取完整的 Redis 鍵"""
        return f"{self.key_prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """獲取快取值"""
        try:
            full_key = self._get_full_key(key)
            data = self.redis_client.get(full_key)
            
            if data is None:
                self.stats.record_miss()
                return None
            
            # 反序列化
            result = json.loads(data)
            self.stats.record_hit()
            return result
            
        except Exception as e:
            self.logger.error(f"Redis 獲取失敗: {key}, 錯誤: {str(e)}", category=LogCategory.CACHE)
            self.stats.record_miss()
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """設置快取值"""
        try:
            full_key = self._get_full_key(key)
            data = json.dumps(value, ensure_ascii=False, default=str)
            
            ttl_value = ttl or self.default_ttl
            result = self.redis_client.setex(full_key, ttl_value, data)
            
            if result:
                self.stats.update_size(self.size())
            
            return result
            
        except Exception as e:
            self.logger.error(f"Redis 設置失敗: {key}, 錯誤: {str(e)}", category=LogCategory.CACHE)
            return False
    
    def delete(self, key: str) -> bool:
        """刪除快取值"""
        try:
            full_key = self._get_full_key(key)
            result = self.redis_client.delete(full_key)
            
            if result:
                self.stats.update_size(self.size())
            
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Redis 刪除失敗: {key}, 錯誤: {str(e)}", category=LogCategory.CACHE)
            return False
    
    def clear(self) -> bool:
        """清空快取"""
        try:
            pattern = f"{self.key_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
            
            self.stats.update_size(0)
            return True
            
        except Exception as e:
            self.logger.error(f"Redis 清空失敗: {str(e)}", category=LogCategory.CACHE)
            return False
    
    def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        try:
            full_key = self._get_full_key(key)
            return bool(self.redis_client.exists(full_key))
            
        except Exception as e:
            self.logger.error(f"Redis 檢查存在失敗: {key}, 錯誤: {str(e)}", category=LogCategory.CACHE)
            return False
    
    def size(self) -> int:
        """獲取快取大小"""
        try:
            pattern = f"{self.key_prefix}*"
            return len(self.redis_client.keys(pattern))
            
        except Exception as e:
            self.logger.error(f"Redis 獲取大小失敗: {str(e)}", category=LogCategory.CACHE)
            return 0


class JobCache:
    """職位搜尋快取管理器"""
    
    def __init__(self, cache_type: CacheType = CacheType.HYBRID,
                 memory_size: int = 500, file_cache_dir: str = "cache",
                 redis_config: Optional[Dict[str, Any]] = None,
                 default_ttl: int = 3600):
        """
        初始化職位快取
        
        Args:
            cache_type: 快取類型
            memory_size: 記憶體快取大小
            file_cache_dir: 檔案快取目錄
            redis_config: Redis 配置
            default_ttl: 預設過期時間（秒）
        """
        self.cache_type = cache_type
        self.default_ttl = default_ttl
        self.logger = get_enhanced_logger("job_cache")
        
        # 初始化快取實例
        self._init_caches(memory_size, file_cache_dir, redis_config)
    
    def _init_caches(self, memory_size: int, file_cache_dir: str, 
                    redis_config: Optional[Dict[str, Any]]):
        """初始化快取實例"""
        if self.cache_type in [CacheType.MEMORY, CacheType.HYBRID]:
            self.memory_cache = MemoryCache(
                max_size=memory_size, 
                default_ttl=self.default_ttl
            )
        
        if self.cache_type in [CacheType.FILE, CacheType.HYBRID]:
            self.file_cache = FileCache(
                cache_dir=file_cache_dir,
                max_size=memory_size * 2,
                default_ttl=self.default_ttl * 24  # 檔案快取保存更久
            )
        
        if self.cache_type == CacheType.REDIS:
            if not redis_config:
                redis_config = {}
            self.redis_cache = RedisCache(
                default_ttl=self.default_ttl,
                **redis_config
            )
    
    def generate_search_key(self, site: Site, search_term: str, 
                           location: str = "", **kwargs) -> str:
        """生成搜尋快取鍵"""
        key_data = {
            'site': site.value,
            'search_term': search_term.lower().strip(),
            'location': location.lower().strip(),
            'filters': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_jobs(self, site: Site, search_term: str, location: str = "", 
                **kwargs) -> Optional[JobResponse]:
        """獲取快取的職位搜尋結果"""
        key = self.generate_search_key(site, search_term, location, **kwargs)
        
        # 嘗試從不同層級的快取獲取
        if self.cache_type == CacheType.MEMORY:
            return self.memory_cache.get(key)
        elif self.cache_type == CacheType.FILE:
            return self._deserialize_job_response(self.file_cache.get(key))
        elif self.cache_type == CacheType.REDIS:
            return self._deserialize_job_response(self.redis_cache.get(key))
        elif self.cache_type == CacheType.HYBRID:
            # 混合模式：先記憶體，再檔案
            result = self.memory_cache.get(key)
            if result is not None:
                return result
            
            result = self._deserialize_job_response(self.file_cache.get(key))
            if result is not None:
                # 將檔案快取的結果放入記憶體快取
                self.memory_cache.set(key, result, ttl=self.default_ttl // 2)
            return result
        
        return None
    
    def set_jobs(self, site: Site, search_term: str, job_response: JobResponse,
                location: str = "", ttl: Optional[int] = None, **kwargs) -> bool:
        """快取職位搜尋結果"""
        key = self.generate_search_key(site, search_term, location, **kwargs)
        ttl = ttl or self.default_ttl
        
        success = True
        
        if self.cache_type == CacheType.MEMORY:
            success = self.memory_cache.set(key, job_response, ttl)
        elif self.cache_type == CacheType.FILE:
            serialized = self._serialize_job_response(job_response)
            success = self.file_cache.set(key, serialized, ttl)
        elif self.cache_type == CacheType.REDIS:
            serialized = self._serialize_job_response(job_response)
            success = self.redis_cache.set(key, serialized, ttl)
        elif self.cache_type == CacheType.HYBRID:
            # 混合模式：同時存入記憶體和檔案快取
            memory_success = self.memory_cache.set(key, job_response, ttl)
            serialized = self._serialize_job_response(job_response)
            file_success = self.file_cache.set(key, serialized, ttl * 24)
            success = memory_success and file_success
        
        if success:
            self.logger.info(
                f"快取職位搜尋結果", 
                category=LogCategory.CACHE,
                site=site.value,
                metadata={
                    'search_term': search_term,
                    'location': location,
                    'jobs_count': len(job_response.jobs) if job_response.jobs else 0,
                    'cache_key': key
                }
            )
        
        return success
    
    def _serialize_job_response(self, job_response: JobResponse) -> Dict[str, Any]:
        """序列化 JobResponse 對象"""
        return {
            'success': job_response.success,
            'error': job_response.error,
            'jobs': [job.model_dump() for job in job_response.jobs] if job_response.jobs else []
        }
    
    def _deserialize_job_response(self, data: Optional[Dict[str, Any]]) -> Optional[JobResponse]:
        """反序列化 JobResponse 對象"""
        if data is None:
            return None
        
        try:
            jobs = [JobPost.model_validate(job_data) for job_data in data.get('jobs', [])]
            return JobResponse(
                success=data.get('success', False),
                error=data.get('error'),
                jobs=jobs
            )
        except Exception as e:
            self.logger.error(f"反序列化 JobResponse 失敗: {str(e)}", category=LogCategory.CACHE)
            return None
    
    def clear_cache(self, site: Optional[Site] = None) -> bool:
        """清空快取"""
        success = True
        
        if self.cache_type == CacheType.MEMORY:
            success = self.memory_cache.clear()
        elif self.cache_type == CacheType.FILE:
            success = self.file_cache.clear()
        elif self.cache_type == CacheType.REDIS:
            success = self.redis_cache.clear()
        elif self.cache_type == CacheType.HYBRID:
            memory_success = self.memory_cache.clear()
            file_success = self.file_cache.clear()
            success = memory_success and file_success
        
        if success:
            site_info = f" for {site.value}" if site else ""
            self.logger.info(f"快取已清空{site_info}", category=LogCategory.CACHE)
        
        return success
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取快取統計資訊"""
        stats = {}
        
        if self.cache_type == CacheType.MEMORY:
            stats['memory'] = self.memory_cache.stats.get_stats()
        elif self.cache_type == CacheType.FILE:
            stats['file'] = self.file_cache.stats.get_stats()
        elif self.cache_type == CacheType.REDIS:
            stats['redis'] = self.redis_cache.stats.get_stats()
        elif self.cache_type == CacheType.HYBRID:
            stats['memory'] = self.memory_cache.stats.get_stats()
            stats['file'] = self.file_cache.stats.get_stats()
        
        return stats
    
    def cleanup_expired(self):
        """清理過期的快取條目"""
        if hasattr(self, 'memory_cache'):
            self.memory_cache.cleanup_expired()
        
        self.logger.info("過期快取清理完成", category=LogCategory.CACHE)


# 全域快取實例
_global_job_cache: Optional[JobCache] = None


def get_job_cache(cache_type: CacheType = CacheType.HYBRID, **kwargs) -> JobCache:
    """獲取全域職位快取實例"""
    global _global_job_cache
    
    if _global_job_cache is None:
        _global_job_cache = JobCache(cache_type=cache_type, **kwargs)
    
    return _global_job_cache


def cache_job_search(cache_type: CacheType = CacheType.HYBRID, ttl: int = 3600):
    """職位搜尋快取裝飾器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 提取搜尋參數
            site = kwargs.get('site') or (args[0] if args else None)
            search_term = kwargs.get('search_term', '')
            location = kwargs.get('location', '')
            
            if not site:
                # 如果沒有網站參數，直接執行函數
                return func(*args, **kwargs)
            
            # 獲取快取
            job_cache = get_job_cache(cache_type)
            
            # 嘗試從快取獲取
            cached_result = job_cache.get_jobs(site, search_term, location, **kwargs)
            if cached_result is not None:
                return cached_result
            
            # 執行函數並快取結果
            result = func(*args, **kwargs)
            if isinstance(result, JobResponse) and result.success:
                job_cache.set_jobs(site, search_term, result, location, ttl, **kwargs)
            
            return result
        
        return wrapper
    return decorator