import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, distinctUntilChanged, map, of, shareReplay, tap } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { UtilsService } from './utils.service';
import { AuthParams } from '../types/OIDC';
import {
  AnalyzerInfo,
  APIDiskUsage,
  APIResponse,
  Constant,
  Identity,
  Info,
  PendingDownloadKey,
  User,
} from '../types/API';
import { Router } from '@angular/router';
import { CaseMetadata } from '../types/case';
import { Collection, CollectionAnalysis, Collector, CollectorSecret, Profile } from '../types/collect';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private utils = inject(UtilsService);
  private http = inject(HttpClient);
  private router = inject(Router);
  public apiBaseUrl: string = '/api';

  private _userSubject$ = new BehaviorSubject<string>('');
  readonly user$ = this._userSubject$.asObservable();

  private infoCache: Info | undefined;
  private constantCache: Constant | undefined;
  private diskUsageData?: { ts: number; du: APIDiskUsage };

  login(data: Object): Observable<APIResponse<User>> {
    return this.http.post<APIResponse<User>>(`${this.apiBaseUrl}/auth/login`, { data }).pipe(
      tap((resp) => {
        if (resp.data) this._userSubject$.next(resp.data.username);
      }),
    );
  }

  unauthorizedRedirectLogin(): void {
    this.router.navigate(['/login']);
  }

  logout(): Observable<APIResponse<null>> {
    return this.http.get<APIResponse<null>>(`${this.apiBaseUrl}/auth/logout`).pipe(
      tap(() => {
        this._userSubject$.next('');
        this.utils.toast('success', 'Logged out', 'Logged out successfully');
        this.router.navigate(['/login']);
      }),
    );
  }

  getAuthParams(): Observable<APIResponse<AuthParams>> {
    return this.http.get<APIResponse<AuthParams>>(`${this.apiBaseUrl}/auth/config`);
  }

  getInfo(): Observable<Info> {
    if (this.infoCache) return of(this.infoCache);
    return this.http.get<APIResponse<Info>>(`${this.apiBaseUrl}/info`).pipe(
      tap((resp) => (this.infoCache = resp.data)),
      map((resp) => resp.data),
    );
  }

  getConstant(): Observable<Constant> {
    if (this.constantCache) return of(this.constantCache);
    return this.http.get<APIResponse<Constant>>(`${this.apiBaseUrl}/constant`).pipe(
      tap((resp) => {
        this.constantCache = resp.data;
        if (resp.data.banner && this.utils.banner !== resp.data.banner) {
          this.utils.banner = resp.data.banner;
        }
      }),
      map((resp) => resp.data),
    );
  }

  isLogged(): Observable<boolean> {
    if (this._userSubject$.value) return of(true);
    return this.http.get<APIResponse<{ username: string }>>(`${this.apiBaseUrl}/auth/is_logged`).pipe(
      tap((resp) => {
        if (resp.data?.username) this._userSubject$.next(resp.data.username);
      }),
      map(() => true),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  getIdentities(): Observable<Identity> {
    return this.http.get<APIResponse<User[]>>(`${this.apiBaseUrl}/auth/identities`).pipe(
      map((resp) => {
        const users = resp.data.map((u) => u.username);
        const groups = Array.from(new Set(resp.data.flatMap((u) => u.groups)));
        return { users, groups };
      }),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  getCase(caseGuid: string): Observable<CaseMetadata> {
    return this.http.get<APIResponse<CaseMetadata>>(`${this.apiBaseUrl}/case/${caseGuid}`).pipe(
      map((resp) => resp.data),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  getCases(): Observable<CaseMetadata[]> {
    return this.http.get<APIResponse<CaseMetadata[]>>(`${this.apiBaseUrl}/cases`).pipe(
      map((resp) => {
        const previous = this.utils.getStoredCaseGuids();
        return resp.data.map((c: CaseMetadata) => ({
          ...c,
          unseenNew: previous.includes(c.guid) ? false : true,
        }));
      }),
      tap((resp) => {
        this.utils.refreshStoredCases(resp);
      }),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  postCase(caseData: CaseMetadata): Observable<CaseMetadata> {
    return this.http.post<APIResponse<CaseMetadata>>(`${this.apiBaseUrl}/case`, caseData).pipe(
      tap((resp) => this.utils.addCaseGuidToStorage(resp.data.guid)),
      map((resp) => resp.data),
    );
  }

  putCase(caseGuid: string, caseData: Partial<CaseMetadata>): Observable<CaseMetadata> {
    return this.http
      .put<APIResponse<CaseMetadata>>(`${this.apiBaseUrl}/case/${caseGuid}`, caseData)
      .pipe(map((resp) => resp.data));
  }

  postCaseCollector(collector: Collector, caseGuid: string): Observable<Collector> {
    return this.http
      .post<APIResponse<Collector>>(`${this.apiBaseUrl}/case/${caseGuid}/collector`, collector)
      .pipe(map((c) => c.data));
  }

  importCaseCollector(collector: Collector, caseGuid: string): Observable<Collector> {
    return this.http
      .post<APIResponse<Collector>>(`${this.apiBaseUrl}/case/${caseGuid}/collector/import`, collector)
      .pipe(map((c) => c.data));
  }

  getCaseCollectors(caseGuid: string): Observable<Collector[]> {
    return this.http
      .get<APIResponse<Collector[]>>(`${this.apiBaseUrl}/case/${caseGuid}/collectors`)
      .pipe(map((c) => c.data));
  }

  getCaseCollectorSecrets(caseGuid: string, collectorGuid: string): Observable<CollectorSecret> {
    return this.http
      .get<APIResponse<CollectorSecret>>(`${this.apiBaseUrl}/case/${caseGuid}/collector/${collectorGuid}/secrets`)
      .pipe(map((c) => c.data));
  }

  downloadCollector(caseGuid: string, collectorGuid: string): Observable<any> {
    return this.http
      .get<APIResponse<PendingDownloadKey>>(`${this.apiBaseUrl}/case/${caseGuid}/collector/${collectorGuid}/download`)
      .pipe(
        map((resp) => {
          window.open(`${this.apiBaseUrl}/download/${resp.data.guid}/${resp.data.token}`, '_blank');
        }),
      );
  }

  getCaseCollections(caseGuid: string): Observable<Collection[]> {
    return this.http
      .get<APIResponse<Collection[]>>(`${this.apiBaseUrl}/case/${caseGuid}/collections`)
      .pipe(map((c) => c.data));
  }

  getCollectionAnalyses(caseGuid: string, collectorGuid: string): Observable<CollectionAnalysis[]> {
    return this.http
      .get<
        APIResponse<CollectionAnalysis[]>
      >(`${this.apiBaseUrl}/case/${caseGuid}/collection/${collectorGuid}/analyses`)
      .pipe(map((c) => c.data));
  }

  getCollectionAnalysisLog(caseGuid: string, collectorGuid: string, analyzerName: string): Observable<string> {
    return this.http.get<string>(
      `${this.apiBaseUrl}/case/${caseGuid}/collection/${collectorGuid}/analysis/${analyzerName}/log`,
      { responseType: 'text' as 'json' },
    );
  }

  postCaseCollection(collection: FormData, caseGuid: string): any {
    return this.http.post<APIResponse<Collector>>(`${this.apiBaseUrl}/case/${caseGuid}/collection`, collection, {
      reportProgress: true,
      observe: 'events',
    });
  }

  putCaseCollection(caseGuid: string, collection: Collection): Observable<Collection> {
    return this.http
      .put<APIResponse<Collection>>(`${this.apiBaseUrl}/case/${caseGuid}/collection/${collection.guid}`, collection)
      .pipe(map((c) => c.data));
  }

  getAnalyzerInfos(): Observable<AnalyzerInfo[]> {
    return this.http.get<APIResponse<AnalyzerInfo[]>>(`${this.apiBaseUrl}/config/analyzers`).pipe(map((c) => c.data));
  }

  getOpsystemProfiles(opSystem: string): Observable<Profile[]> {
    return this.http
      .get<APIResponse<Profile[]>>(`${this.apiBaseUrl}/config/${opSystem}/profiles`)
      .pipe(map((c) => c.data));
  }

  postCollectionAnalysis(
    caseGuid: string,
    collectionGuid: string,
    analysis: Partial<CollectionAnalysis>,
  ): Observable<CollectionAnalysis> {
    return this.http
      .post<
        APIResponse<CollectionAnalysis>
      >(`${this.apiBaseUrl}/case/${caseGuid}/collection/${collectionGuid}/analysis`, analysis)
      .pipe(map((c) => c.data));
  }

  putCollectionAnalysis(
    caseGuid: string,
    collectionGuid: string,
    analyzerName: string,
    analysisData: Partial<CollectionAnalysis>,
  ): Observable<CollectionAnalysis> {
    return this.http
      .put<
        APIResponse<CollectionAnalysis>
      >(`${this.apiBaseUrl}/case/${caseGuid}/collection/${collectionGuid}/analysis/${analyzerName}`, analysisData)
      .pipe(map((c) => c.data));
  }

  downloadCollection(caseGuid: string, collectionGuid: string): Observable<any> {
    return this.http
      .get<APIResponse<any>>(`${this.apiBaseUrl}/case/${caseGuid}/collection/${collectionGuid}/download`)
      .pipe(
        map((resp) => {
          window.open(`${this.apiBaseUrl}/download/${resp.data.guid}/${resp.data.token}`, '_blank');
        }),
      );
  }

  removeCache(caseGuid: string, collectionGuid: string): Observable<{}> {
    return this.http.delete<APIResponse<any>>(`${this.apiBaseUrl}/case/${caseGuid}/collection/${collectionGuid}/cache`);
  }

  downloadCollectionAnalysis(caseGuid: string, collectionGuid: string, analyzerName: string): Observable<any> {
    return this.http
      .get<
        APIResponse<any>
      >(`${this.apiBaseUrl}/case/${caseGuid}/collection/${collectionGuid}/analysis/${analyzerName}/download`)
      .pipe(
        map((resp) => {
          window.open(`${this.apiBaseUrl}/download/${resp.data.guid}/${resp.data.token}`, '_blank');
        }),
      );
  }

  getDiskUsage(): Observable<APIDiskUsage> {
    const observable = this.http.get<APIResponse<APIDiskUsage>>(`${this.apiBaseUrl}/disk_usage`).pipe(
      map((c) => c.data),
      tap((data) => {
        this.diskUsageData = { ts: new Date().getTime(), du: data };
      }),
    );

    if (!this.diskUsageData) return observable;
    if (new Date().getTime() - this.diskUsageData.ts > 60000 * 5) return observable;
    return of(this.diskUsageData.du);
  }
}
