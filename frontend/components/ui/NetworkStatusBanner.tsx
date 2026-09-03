'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Wifi,
  WifiOff,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  UploadCloud,
  ChevronDown,
  ChevronUp,
  X
} from 'lucide-react';
import { OfflineEvidenceQueue, OfflineQueueItem } from '../../lib/offlineQueue';

export const NetworkStatusBanner: React.FC = () => {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [queueItems, setQueueItems] = useState<OfflineQueueItem[]>([]);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [showDrawer, setShowDrawer] = useState<boolean>(false);
  const [lastSyncMessage, setLastSyncMessage] = useState<string | null>(null);

  const refreshQueueState = useCallback(() => {
    setQueueItems(OfflineEvidenceQueue.getItems());
  }, []);

  useEffect(() => {
    setIsOnline(navigator.onLine);
    refreshQueueState();

    const handleOnline = () => {
      setIsOnline(true);
      // Auto-trigger sync upon reconnection
      handleSync();
    };

    const handleOffline = () => {
      setIsOnline(false);
      refreshQueueState();
    };

    const handleQueueUpdated = () => {
      refreshQueueState();
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('legalmetrix_queue_updated', handleQueueUpdated);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('legalmetrix_queue_updated', handleQueueUpdated);
    };
  }, [refreshQueueState]);

  const handleSync = async () => {
    if (!navigator.onLine || syncing) return;
    setSyncing(true);
    setLastSyncMessage(null);
    try {
      const res = await OfflineEvidenceQueue.syncQueue(
        (item, uploaded) => {
          console.log(`Synced ${item.viewType} evidence for case ${item.inspectionId}: SHA-256 ${uploaded.sha256}`);
        },
        (item, error) => {
          console.warn(`Failed syncing ${item.viewType} for case ${item.inspectionId}: ${error}`);
        }
      );
      if (res.synced > 0) {
        setLastSyncMessage(`Synchronized ${res.synced} evidence item(s) successfully.`);
      }
      refreshQueueState();
    } catch (e) {
      console.error('Sync failed:', e);
    } finally {
      setSyncing(false);
    }
  };

  const pendingCount = queueItems.filter(
    (i) => i.syncStatus === 'PENDING' || i.syncStatus === 'FAILED' || i.syncStatus === 'RETRY_REQUIRED'
  ).length;

  const failedCount = queueItems.filter((i) => i.syncStatus === 'FAILED').length;

  // Render minimal bar if online and no pending items
  if (isOnline && pendingCount === 0 && !lastSyncMessage) {
    return null;
  }

  return (
    <div className="bg-slate-900 text-white border-b border-slate-800 text-xs px-4 py-2.5 transition-all">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-2.5">
          {!isOnline ? (
            <span className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold text-[11px]">
              <WifiOff className="w-3.5 h-3.5" />
              <span>OFFLINE FIELD MODE</span>
            </span>
          ) : (
            <span className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold text-[11px]">
              <Wifi className="w-3.5 h-3.5" />
              <span>ONLINE</span>
            </span>
          )}

          <div className="text-slate-300 text-xs">
            {!isOnline ? (
              <span>Captured evidence will be preserved in durable local queue until network is restored.</span>
            ) : pendingCount > 0 ? (
              <span>
                <strong className="text-white">{pendingCount}</strong> evidence item(s) pending synchronization.
              </span>
            ) : (
              <span className="text-emerald-300">{lastSyncMessage}</span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {queueItems.length > 0 && (
            <button
              onClick={() => setShowDrawer(!showDrawer)}
              className="text-[11px] text-slate-300 hover:text-white px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 transition-colors inline-flex items-center space-x-1"
            >
              <span>Queue ({queueItems.length})</span>
              {showDrawer ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
          )}

          {isOnline && pendingCount > 0 && (
            <button
              onClick={handleSync}
              disabled={syncing}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded font-bold text-xs inline-flex items-center space-x-1.5 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 ${syncing ? 'animate-spin' : ''}`} />
              <span>{syncing ? 'Syncing...' : 'Sync Evidence Now'}</span>
            </button>
          )}

          {lastSyncMessage && pendingCount === 0 && (
            <button
              onClick={() => setLastSyncMessage(null)}
              className="text-slate-400 hover:text-slate-200"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Drawer showing queue contents */}
      {showDrawer && queueItems.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-800 max-w-7xl mx-auto space-y-2">
          <div className="flex items-center justify-between text-[11px] text-slate-400 font-semibold uppercase">
            <span>Local Evidence Capture Queue</span>
            <button
              onClick={() => {
                OfflineEvidenceQueue.clearSynced();
                refreshQueueState();
              }}
              className="hover:text-slate-200 text-slate-400"
            >
              Clear Synced Items
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-48 overflow-y-auto">
            {queueItems.map((item) => (
              <div
                key={item.localQueueId}
                className="bg-slate-800/80 border border-slate-700 rounded p-2 text-xs flex items-center justify-between space-x-2"
              >
                <div className="truncate">
                  <div className="font-semibold text-slate-200">{item.viewType} Panel View</div>
                  <div className="text-[10px] text-slate-400 truncate">Case: {item.inspectionId}</div>
                  {item.lastError && (
                    <div className="text-[10px] text-rose-400 truncate">{item.lastError}</div>
                  )}
                </div>
                <div className="flex items-center space-x-1.5 shrink-0">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      item.syncStatus === 'SYNCED'
                        ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-700'
                        : item.syncStatus === 'FAILED'
                        ? 'bg-rose-900/60 text-rose-300 border border-rose-700'
                        : item.syncStatus === 'UPLOADING'
                        ? 'bg-blue-900/60 text-blue-300 border border-blue-700'
                        : 'bg-amber-900/60 text-amber-300 border border-amber-700'
                    }`}
                  >
                    {item.syncStatus}
                  </span>
                  {item.syncStatus === 'FAILED' && (
                    <button
                      onClick={() => {
                        OfflineEvidenceQueue.retryItem(item.localQueueId);
                        refreshQueueState();
                      }}
                      className="p-1 hover:bg-slate-700 rounded text-slate-300"
                      title="Retry sync"
                    >
                      <RefreshCw className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
