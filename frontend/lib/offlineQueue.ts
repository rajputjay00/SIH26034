import { EvidenceViewType, EvidenceItem } from '../types';
import { uploadEvidence } from './api';

export type SyncStatus = 'PENDING' | 'UPLOADING' | 'SYNCED' | 'FAILED' | 'RETRY_REQUIRED';

export interface OfflineQueueItem {
  localQueueId: string;
  inspectionId: string;
  viewType: EvidenceViewType;
  filename: string;
  dataUrl: string; // Base64 image representation for durable local storage
  sizeBytes: number;
  mimeType: string;
  createdAt: string;
  syncStatus: SyncStatus;
  retryCount: number;
  lastError?: string;
  syncedEvidenceId?: string;
  syncedSha256?: string;
}

const STORAGE_KEY = 'legalmetrix_offline_evidence_queue';

export class OfflineEvidenceQueue {
  private static isClient(): boolean {
    return typeof window !== 'undefined' && typeof localStorage !== 'undefined';
  }

  public static getItems(): OfflineQueueItem[] {
    if (!this.isClient()) return [];
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      console.error('Failed to read offline evidence queue:', e);
      return [];
    }
  }

  public static saveItems(items: OfflineQueueItem[]): void {
    if (!this.isClient()) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
      // Dispatch custom event so UI components update reactively
      window.dispatchEvent(new CustomEvent('legalmetrix_queue_updated'));
    } catch (e) {
      console.error('Failed to persist offline evidence queue:', e);
    }
  }

  public static async enqueue(
    inspectionId: string,
    viewType: EvidenceViewType,
    file: File
  ): Promise<OfflineQueueItem> {
    const dataUrl = await this.fileToDataUrl(file);
    const item: OfflineQueueItem = {
      localQueueId: `queue_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`,
      inspectionId,
      viewType,
      filename: file.name,
      dataUrl,
      sizeBytes: file.size,
      mimeType: file.type || 'image/jpeg',
      createdAt: new Date().toISOString(),
      syncStatus: 'PENDING',
      retryCount: 0
    };

    const items = this.getItems();
    items.unshift(item);
    this.saveItems(items);
    return item;
  }

  public static getPendingCount(): number {
    return this.getItems().filter(
      (item) => item.syncStatus === 'PENDING' || item.syncStatus === 'FAILED' || item.syncStatus === 'RETRY_REQUIRED'
    ).length;
  }

  public static async syncQueue(
    onItemSuccess?: (item: OfflineQueueItem, result: EvidenceItem) => void,
    onItemError?: (item: OfflineQueueItem, error: string) => void
  ): Promise<{ synced: number; failed: number }> {
    if (!this.isClient() || !navigator.onLine) {
      return { synced: 0, failed: 0 };
    }

    const items = this.getItems();
    let synced = 0;
    let failed = 0;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.syncStatus === 'SYNCED') continue;

      try {
        item.syncStatus = 'UPLOADING';
        this.saveItems(items);

        // Convert base64 dataUrl back to File
        const file = this.dataUrlToFile(item.dataUrl, item.filename, item.mimeType);

        // Server-side authoritative upload & hashing
        const uploaded = await uploadEvidence(item.inspectionId, file, item.viewType);

        item.syncStatus = 'SYNCED';
        item.syncedEvidenceId = uploaded.evidence_id;
        item.syncedSha256 = uploaded.sha256;
        synced++;

        if (onItemSuccess) {
          onItemSuccess(item, uploaded);
        }
      } catch (err: unknown) {
        const errorMsg = err instanceof Error ? err.message : 'Upload failed during synchronization';
        item.syncStatus = 'FAILED';
        item.retryCount += 1;
        item.lastError = errorMsg;
        failed++;

        if (onItemError) {
          onItemError(item, errorMsg);
        }
      }
      this.saveItems(items);
    }

    return { synced, failed };
  }

  public static retryItem(localQueueId: string): void {
    const items = this.getItems();
    const target = items.find((i) => i.localQueueId === localQueueId);
    if (target) {
      target.syncStatus = 'PENDING';
      target.lastError = undefined;
      this.saveItems(items);
    }
  }

  public static removeItem(localQueueId: string): void {
    const items = this.getItems().filter((i) => i.localQueueId !== localQueueId);
    this.saveItems(items);
  }

  public static clearSynced(): void {
    const items = this.getItems().filter((i) => i.syncStatus !== 'SYNCED');
    this.saveItems(items);
  }

  private static fileToDataUrl(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  private static dataUrlToFile(dataUrl: string, filename: string, mimeType: string): File {
    const arr = dataUrl.split(',');
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mimeType });
  }
}
