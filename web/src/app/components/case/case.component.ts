import { ChangeDetectorRef, Component, ElementRef, HostListener, OnDestroy, ViewChild } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { FloatLabelModule } from 'primeng/floatlabel';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TextareaModule } from 'primeng/textarea';
import { SkeletonModule } from 'primeng/skeleton';
import { FocusTrapModule } from 'primeng/focustrap';
import { ApiService } from '../../services/api.service';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Collection, CollectionAnalysis, Collector } from '../../types/collect';
import { FileSizePipe } from '../../shared/filesize.pipe';
import { ClipboardModule } from '@angular/cdk/clipboard';
import { DialogService } from 'primeng/dynamicdialog';
import { CollectorCreateModalComponent } from '../../modals/collector-create-modal/collector-create-modal.component';
import { CollectorImportModalComponent } from '../../modals/collector-import-modal/collector-import-modal.component';
import { Menu, MenuModule } from 'primeng/menu';
import { MenuItem } from 'primeng/api';
import { TooltipModule } from 'primeng/tooltip';
import { CaseMetadata, FusionEvent } from '../../types/case';
import { UtilsService } from '../../services/utils.service';
import { HttpErrorResponse, HttpEvent, HttpEventType } from '@angular/common/http';
import { APIResponse, AnalyzerInfo } from '../../types/API';
import { DatePipe, KeyValuePipe } from '@angular/common';
import { MessageModule } from 'primeng/message';
import { CollectionEditModalComponent } from '../../modals/collection-edit-modal/collection-edit-modal.component';
import { CollectorSecretsModalComponent } from '../../modals/collector-secrets-modal/collector-secrets-modal.component';
import { TabsModule } from 'primeng/tabs';
import { CollectionLogsModalComponent } from '../../modals/collection-logs-modal/collection-logs-modal.component';
import { CaseCreateModalComponent } from '../../modals/case-create-modal/case-create-modal.component';
import { Subscription, take } from 'rxjs';
import { YesNoModalComponent } from '../../modals/yes-no-modal/yes-no-modal.component';
import { DeleteConfirmModalComponent } from '../../modals/delete-confirm-modal/delete-confirm-modal.component';

@Component({
  selector: 'app-case',
  standalone: true,
  imports: [
    RouterLink,
    FloatLabelModule,
    InputTextModule,
    ButtonModule,
    SelectModule,
    ReactiveFormsModule,
    TabsModule,
    TooltipModule,
    FileSizePipe,
    TextareaModule,
    FocusTrapModule,
    MessageModule,
    SkeletonModule,
    ClipboardModule,
    MenuModule,
    DatePipe,
    ButtonModule,
    KeyValuePipe,
  ],
  templateUrl: './case.component.html',
  styleUrl: './case.component.scss',
})
export class CaseComponent implements OnDestroy {
  @ViewChild('collectionTabContent') collectionTabContentRef?: ElementRef;
  @ViewChild('actionsMenu') actionsMenu!: Menu;
  @ViewChild('caseMenu') caseMenu!: Menu;

  @HostListener('document:dragenter', ['$event'])
  onDragEnter(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
    this.dragTarget = event.target;
  }

  @HostListener('document:dragleave', ['$event'])
  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    if (event.target === this.dragTarget || event.target === document) {
      this.isDragging = false;
    }
  }

  @HostListener('document:dragover', ['$event'])
  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
  }

  @HostListener('document:drop', ['$event'])
  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
    if (event.dataTransfer?.files) {
      this.uploadCollection(event.dataTransfer?.files[0]);
    }
  }

  isDragging: boolean = false;
  dragTarget: EventTarget | null = null;
  caseForm: FormGroup;
  caseMeta: CaseMetadata | undefined;
  caseDiskUsage: { [c: string]: number } = {};
  caseCollectors: Collector[] = [];
  caseCollections: Collection[] = [];
  selectedCollectionTabID: string = '';
  displayedCollections: Collection[] = [];
  uploadProgress = '';
  analyses: { [guid: string]: { [analyzerName: string]: CollectionAnalysis } } = {};
  analyzerInfos: AnalyzerInfo[] = [];
  eventSource!: Subscription;
  activeUsers: string[] = [];

  actionsMenuItems: MenuItem[] = [];
  caseMenuItems: MenuItem[] = [];

  constructor(
    private apiService: ApiService,
    private cdr: ChangeDetectorRef,
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private utilsService: UtilsService,
    private dialogService: DialogService,
  ) {
    this.caseForm = this.fb.group({
      tsid: '',
      name: ['', Validators.required],
      description: '',
    });

    this.apiService
      .getCase(this.route.snapshot.paramMap.get('id')!)
      .pipe(take(1))
      .subscribe({
        next: (caseMeta) => {
          this.caseMeta = caseMeta;

          this.eventSource = this.apiService.getCaseEventsSSE(this.caseMeta!.guid).subscribe({
            next: (event) => this.handleSSEEvent(event),
            error: (error) => console.error('SSE error:', error),
          });

          this.apiService
            .getCaseCollectors(this.caseMeta.guid)
            .pipe(take(1))
            .subscribe({
              next: (collectors) => {
                this.caseCollectors = collectors;
                this.sortCollectors();
              },
              error: () => this.utilsService.navigateHomeWithError('Error while retrieving collectors'),
            });

          this.apiService
            .getCaseCollections(this.caseMeta.guid)
            .pipe(take(1))
            .subscribe({
              next: (collections) => {
                this.caseCollections = collections;
                this.sortCollections();
              },
            });

          this.apiService
            .getDiskUsage()
            .pipe(take(1))
            .subscribe({
              next: (diskUsage) => {
                const du = diskUsage.cases.find((c) => c.guid == caseMeta.guid);
                if (!du) return;
                Object.entries(du).forEach(([k, v]) => (this.caseDiskUsage[k] = v));
                this.caseDiskUsage['_total'] = du.analyses + du.collections + du.collectors;
              },
            });
        },
        error: () => this.utilsService.navigateHomeWithError('Error while retrieving case'),
      });

    this.apiService
      .getAnalyzerInfos()
      .pipe(take(1))
      .subscribe({
        next: (analyzerInfos) => (this.analyzerInfos = analyzerInfos),
      });
  }

  ngOnDestroy(): void {
    if (this.eventSource) this.eventSource.unsubscribe();
  }

  handleSSEEvent(messageEvent: MessageEvent): void {
    if (!messageEvent.data) return;
    const event: FusionEvent = JSON.parse(messageEvent.data);
    const ext = event.ext;
    switch (event.category) {
      case 'subscribers':
        this.activeUsers = ext.usernames;
        break;
      case 'subscribe':
        if (!this.activeUsers.includes(ext.username)) this.activeUsers.push(ext.username);
        break;
      case 'unsubscribe':
        this.activeUsers = this.activeUsers.filter((u) => u !== ext.username);
        break;
      case 'import_collector':
        this.caseCollectors = [...this.caseCollectors, ext];
        this.sortCollectors();
        break;
      case 'create_collector':
        this.caseCollectors = [...this.caseCollectors, ext];
        this.sortCollectors();
        break;
      case 'delete_collector':
        this.caseCollectors = this.caseCollectors.filter((c) => c.guid != ext.guid);
        this.utilsService.toast('info', 'A collector was deleted', 'A collector was deleted');
        break;
      case 'create_collection':
        this.caseCollections = [...this.caseCollections, ext];
        this.sortCollections();
        break;
      case 'update_collection': {
        this.caseCollections = [...this.caseCollections.filter((c) => c.guid != ext.guid), ext];
        const index_update_collection = this.displayedCollections.findIndex((c) => c.guid == ext.guid);
        if (index_update_collection > -1)
          this.displayedCollections = [...this.displayedCollections.filter((c) => c.guid != ext.guid), ext];
        this.sortCollections();
        break;
      }
      case 'delete_collection':
        const collectionId = ext.guid;
        this.caseCollections = this.caseCollections.filter((c) => c.guid != collectionId);
        const index = this.displayedCollections.findIndex((c) => c.guid == collectionId);
        if (index > -1) {
          this.displayedCollections = this.displayedCollections.filter((c) => c.guid != collectionId);
          const selectedTabID = this.selectedCollectionTabID;
          this.selectedCollectionTabID = '';
          setTimeout(() => {
            this.selectedCollectionTabID =
              selectedTabID == collectionId ? this.displayedCollections[0]?.guid || '' : selectedTabID;
            this.collectionTabContentRef?.nativeElement.scrollIntoView({
              block: 'start',
              behavior: 'smooth',
            });
          }, 10);
        }
        break;
      case 'update_case':
        this.caseMeta = event.case;
        break;
      case 'delete_case':
        this.utilsService.toast('info', 'Case deleted', 'This case was deleted');
        this.utilsService.navigateHomeWithError();
        break;
      case 'create_analysis': {
        const collection = ext.collection;
        const analysis = ext.analysis;
        if (this.analyses.hasOwnProperty(collection.guid)) this.analyses[collection.guid][analysis.analyzer] = analysis;
        break;
      }
      case 'delete_analysis':
        Object.entries(this.analyses).forEach(([collectionGuid, analyses]) => {
          Object.entries(analyses).forEach(([analyzerName, analysis]) => {
            if (analysis.guid == ext.guid) delete this.analyses[collectionGuid][analyzerName];
          });
        });
        break;
      default: {
        if (!event.category.startsWith('analysis_')) break;
        const collection = ext.collection;
        const analysis = ext.analysis;
        const status = event.category.split('analysis_')[1];
        if (this.analyses.hasOwnProperty(collection.guid))
          this.analyses[collection.guid][analysis.analyzer] = { ...analysis, status };
      }
    }
    this.cdr.markForCheck();
  }

  isCollectionOrphaned(collection: Collection): boolean {
    return !this.caseCollectors.some((c) => c.fingerprint == collection.fingerprint);
  }

  openEditCaseModal() {
    const modal = this.dialogService.open(CaseCreateModalComponent, {
      header: 'Update Case',
      modal: true,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '30vw',
      data: this.caseMeta,
      breakpoints: {
        '960px': '90vw',
      },
    });

    modal.onClose.pipe(take(1)).subscribe((data: CaseMetadata | null) => {
      if (!data) return;
      this.putCase(data);
    });
  }

  putCase(data: Partial<CaseMetadata>) {
    this.apiService.putCase(this.caseMeta!.guid, data).pipe(take(1)).subscribe();
  }

  sortCollectors() {
    this.caseCollectors.sort(
      (a, b) => new Date(b.created as string).getTime() - new Date(a.created as string).getTime(),
    );
  }

  sortCollections() {
    this.caseCollections.sort(
      (a, b) => new Date(b.created as string).getTime() - new Date(a.created as string).getTime(),
    );
  }

  openCollection(guid: string) {
    const alreadyOpenedCollectionIndex = this.displayedCollections.findIndex((s) => s.guid == guid);
    if (alreadyOpenedCollectionIndex === -1) {
      const collection = this.caseCollections.find((c) => c.guid == guid);
      if (collection) {
        this.displayedCollections = [...this.displayedCollections, collection];
      }
    }

    setTimeout(() => {
      if (this.collectionTabContentRef?.nativeElement) {
        this.collectionTabContentRef?.nativeElement.scrollIntoView({
          block: 'start',
          behavior: 'smooth',
        });
      }
    }, 10);
    this.selectedCollectionTabID = guid;
    this.apiService
      .getCollectionAnalyses(this.caseMeta!.guid, guid)
      .pipe(take(1))
      .subscribe({
        next: (analyses) => {
          this.analyses[guid] = Object.fromEntries(analyses.map((a) => [a.analyzer, a]));
        },
      });
  }

  closeDisplayedCollection(index: number) {
    this.displayedCollections.splice(index, 1);
    this.selectedCollectionTabID = ''; // HACK: PrimeNG Tabs are not reconstructed otherwise
    setTimeout(() => {
      this.selectedCollectionTabID = this.displayedCollections[0]?.guid || '';
      this.collectionTabContentRef?.nativeElement.scrollIntoView({
        block: 'start',
        behavior: 'smooth',
      });
    }, 10);
  }

  constructMenu(ev: any, analysisGuid: string, analyzerName: string, collection: Collection) {
    const status = this.analyses[analysisGuid][analyzerName]
      ? this.analyses[analysisGuid][analyzerName].status
      : undefined;
    const items: MenuItem[] = [];

    const LOG = {
      label: 'Logs',
      icon: 'pi pi-paperclip',
      command: () => this.getCollectionLog(analysisGuid, analyzerName),
    };

    const RESTART = {
      label: 'Restart',
      icon: 'pi pi-replay',
      command: () => this.restartAnalysis(analysisGuid, analyzerName),
    };

    const DELETE = {
      label: 'Delete',
      icon: 'pi pi-trash',
      command: () => this.deleteAnalysis(analysisGuid, analyzerName),
    };

    switch (status) {
      case 'failure':
        items.push(RESTART);
        items.push(LOG);
        items.push(DELETE);
        break;

      case 'success':
        items.push(RESTART);
        items.push(LOG);
        items.push(DELETE);
        items.push({
          label: 'Download',
          icon: 'pi pi-download',
          command: () => this.downloadAnalysis(analysisGuid, analyzerName),
        });
        break;

      case 'pending':
      case 'processing':
        items.push(LOG);
        break;

      default:
        items.push({
          label: 'Start',
          icon: 'pi pi-play',
          disabled: this.isCollectionOrphaned(collection),
          command: () => this.startAnalysis(analysisGuid, analyzerName),
        });
        break;
    }

    this.actionsMenuItems = [
      {
        label: analyzerName,
        items: items,
      },
    ];
    this.actionsMenu.toggle(ev);
  }

  tagIntersect(analyzerName: string, tags: string[]): boolean {
    const analyzerInfo = this.analyzerInfos.find((analyzerInfo) => analyzerInfo.name == analyzerName);
    if (!analyzerInfo) return false;
    return !analyzerInfo.tags.length || (tags && tags.some(Set.prototype.has, new Set(analyzerInfo.tags)));
  }

  startAnalysis(guid: string, analyzerName: string) {
    const analysis: Partial<CollectionAnalysis> = { analyzer: analyzerName };
    this.apiService
      .postCollectionAnalysis(this.caseMeta!.guid, guid, analysis)
      .pipe(take(1))
      .subscribe({
        next: (analysis) => (this.analyses[guid][analysis.analyzer] = analysis),
      });
  }

  restartAnalysis(guid: string, analyzerName: string) {
    this.apiService
      .putCollectionAnalysis(this.caseMeta!.guid, guid, analyzerName, {})
      .pipe(take(1))
      .subscribe({
        next: (analysis) => (this.analyses[guid][analysis.analyzer] = analysis),
      });
  }

  downloadAnalysis(guid: string, analyzerName: string) {
    this.apiService.downloadCollectionAnalysis(this.caseMeta!.guid, guid, analyzerName).pipe(take(1)).subscribe();
  }

  refreshAnalyses(guid: string) {
    const iconElement = document.getElementById('refreshAnalysesIcon');
    iconElement?.classList.add('spin-once');
    setTimeout(() => {
      iconElement?.classList.remove('spin-once');
    }, 1000);

    this.apiService
      .getCollectionAnalyses(this.caseMeta!.guid, guid)
      .pipe(take(1))
      .subscribe({
        next: (analyses) => (this.analyses[guid] = Object.fromEntries(analyses.map((a) => [a.analyzer, a]))),
      });
  }

  constructCaseMenu(ev: any) {
    if (!this.caseMeta) return;
    const closeOrReopenItem = this.caseMeta.closed
      ? {
          label: 'Reopen',
          icon: 'pi pi-lock-open',
          iconClass: 'text-green-500!',
          command: () =>
            this.apiService
              .putCase(this.caseMeta!.guid, { closed: '' })
              .pipe(take(1))
              .subscribe({
                next: (meta) => (this.caseMeta = meta),
              }),
        }
      : {
          label: 'Close',
          icon: 'pi pi-times',
          iconClass: 'text-red-500!',
          command: () =>
            this.apiService
              .putCase(this.caseMeta!.guid, { closed: new Date().toISOString() })
              .pipe(take(1))
              .subscribe({
                next: (meta) => (this.caseMeta = meta),
              }),
        };

    this.caseMenuItems = [
      {
        label: 'Copy GUID',
        icon: 'pi pi-tag',
        command: () => {
          try {
            navigator.clipboard.writeText(this.caseMeta!.guid);
          } catch {
            console.error('Clipboard not available');
            this.utilsService.toast('error', 'Error', 'Clipboard not available');
          }
        },
      },
      {
        label: 'Edit',
        icon: 'pi pi-pencil',
        disabled: !!this.caseMeta.closed,
        command: () => this.openEditCaseModal(),
      },
      closeOrReopenItem,
      {
        label: 'Delete',
        icon: 'pi pi-trash',
        iconClass: 'text-red-500!',
        command: () => this.deleteCase(),
      },
    ];

    this.caseMenu.toggle(ev);
  }

  importCollector() {
    const modal = this.dialogService.open(CollectorImportModalComponent, {
      header: 'Import Collector',
      modal: true,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '30vw',
      breakpoints: {
        '960px': '90vw',
      },
    });

    modal.onClose.pipe(take(1)).subscribe((collector: Collector | null) => {
      if (!collector) return;
      this.apiService.importCaseCollector(collector, this.caseMeta?.guid!).pipe(take(1)).subscribe();
    });
  }

  addCollector() {
    const modal = this.dialogService.open(CollectorCreateModalComponent, {
      header: 'Create Collector',
      modal: true,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '30vw',
      breakpoints: {
        '960px': '90vw',
      },
    });

    modal.onClose.pipe(take(1)).subscribe((collector: Collector | null) => {
      if (!collector) return;
      this.apiService.postCaseCollector(collector, this.caseMeta?.guid!).pipe(take(1)).subscribe();
    });
  }

  onCollectionUpload(ev: any) {
    if (ev.target.files[0]) this.uploadCollection(ev.target.files[0]);
  }

  refreshCollections() {
    const iconElement = document.getElementById('refreshIcon');
    iconElement?.classList.add('spin-once');
    setTimeout(() => {
      iconElement?.classList.remove('spin-once');
    }, 1000);
    this.apiService
      .getCaseCollections(this.caseMeta!.guid)
      .pipe(take(1))
      .subscribe({
        next: (collections) => {
          this.caseCollections = collections;
          this.sortCollections();
        },
      });
  }

  uploadCollection(file: File) {
    const modal = this.dialogService.open(YesNoModalComponent, {
      header: 'Upload Collection',
      modal: true,
      closable: true,
      dismissableMask: true,
      breakpoints: {
        '640px': '90vw',
      },
      data: {
        msg: `Confirm with ${file.name} upload ?`,
        warning: file.name.endsWith('.zip') ? '' : 'Helium supports zip and your file extension is mismatching',
      },
    });

    modal.onClose.pipe(take(1)).subscribe({
      next: (bool) => {
        if (!bool) return;

        const formdata = new FormData();
        formdata.append('file', file, file.name);

        this.apiService.postCaseCollection(formdata, this.caseMeta!.guid).subscribe({
          next: (event: HttpEvent<any>) => {
            switch (event.type) {
              case HttpEventType.UploadProgress:
                if (event.total) {
                  let progress = Math.round((100 * event.loaded) / event.total);

                  if (progress == 100) this.uploadProgress = `[100%] Processing file`;
                  else this.uploadProgress = `[${progress}%] ${file.name}`;
                }
                break;

              case HttpEventType.Response:
                let collection = (event.body as APIResponse<Collection>)['data'];
                this.uploadProgress = '';
                const modal = this.dialogService.open(CollectionEditModalComponent, {
                  header: 'Edit Collection',
                  modal: true,
                  appendTo: 'body',
                  closable: true,
                  dismissableMask: true,
                  width: '30vw',
                  breakpoints: {
                    '960px': '90vw',
                  },
                  data: {
                    collection: collection,
                    filename: file.name,
                  },
                });

                modal.onClose.pipe(take(1)).subscribe((pCollection: Collection | null) => {
                  if (pCollection)
                    this.apiService.putCaseCollection(this.caseMeta!.guid, pCollection).pipe(take(1)).subscribe();
                  else this.caseCollections.push(collection);
                });
                break;
            }
          },
          error: (error: HttpErrorResponse) => console.error(error),
        });
      },
    });
  }

  getCollectionLog(guid: string, analyzerName: string) {
    this.apiService
      .getCollectionAnalysisLog(this.caseMeta!.guid, guid, analyzerName)
      .pipe(take(1))
      .subscribe({
        next: (content) => {
          this.dialogService.open(CollectionLogsModalComponent, {
            header: `${analyzerName} logs`,
            modal: true,
            appendTo: 'body',
            closable: true,
            dismissableMask: true,
            width: '45vw',
            breakpoints: {
              '960px': '90vw',
            },
            data: content,
          });
        },
      });
  }

  getCollectorSecrets(collector: Collector) {
    this.dialogService.open(CollectorSecretsModalComponent, {
      header: 'Collector Secrets',
      modal: true,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '45vw',
      breakpoints: {
        '960px': '90vw',
      },
      data: {
        guid: this.caseMeta!.guid,
        collector: collector.guid,
        fingerprint: collector.fingerprint,
      },
    });
  }

  editCollection(collection: Collection) {
    const modal = this.dialogService.open(CollectionEditModalComponent, {
      header: 'Edit Collection',
      modal: true,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '30vw',
      breakpoints: {
        '960px': '90vw',
      },
      data: {
        collection: collection,
        filename: '',
      },
    });

    modal.onClose.pipe(take(1)).subscribe((pCollection: Collection | null) => {
      if (pCollection) this.apiService.putCaseCollection(this.caseMeta!.guid, pCollection).pipe(take(1)).subscribe();
    });
  }

  removeCache(collectionGuid: string) {
    const modal = this.dialogService.open(YesNoModalComponent, {
      header: 'Remove cache',
      modal: true,
      closable: true,
      dismissableMask: true,
      breakpoints: {
        '640px': '90vw',
      },
      data: {
        msg: 'You are about to remove cache to free space, including decrypted collections',
        warning: 'Analyzers will need to decrypt collection again',
      },
    });

    modal.onClose.pipe(take(1)).subscribe({
      next: (bool) => {
        if (!bool) return;

        this.apiService
          .removeCache(this.caseMeta!.guid, collectionGuid)
          .pipe(take(1))
          .subscribe({
            next: () => this.utilsService.toast('success', 'Success', 'Cache removed'),
          });
      },
    });
  }

  downloadCollector(collectorGuid: string): void {
    this.apiService
      .downloadCollector(this.caseMeta!.guid, collectorGuid)
      .pipe(take(1))
      .subscribe({
        error: (error) => console.error(error),
      });
  }

  downloadCollection(collectionGuid: string): void {
    this.apiService
      .downloadCollection(this.caseMeta!.guid, collectionGuid)
      .pipe(take(1))
      .subscribe({
        error: (error) => console.error(error),
      });
  }

  deleteAnalysis(guid: string, analyzerName: string) {
    this.apiService
      .deleteCollectionAnalysis(this.caseMeta!.guid, guid, analyzerName)
      .pipe(take(1))
      .subscribe({
        next: () => {
          this.apiService.getCollectionAnalyses(this.caseMeta!.guid, guid).pipe(take(1)).subscribe();
        },
      });
  }

  deleteCase() {
    if (!this.caseMeta || !this.caseMeta.name) return;
    const modal = this.dialogService.open(DeleteConfirmModalComponent, {
      header: 'Confirm to delete',
      modal: true,
      closable: true,
      dismissableMask: true,
      breakpoints: {
        '640px': '90vw',
      },
      data: this.caseMeta?.name,
    });

    modal.onClose.pipe(take(1)).subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.apiService.deleteCase(this.caseMeta!.guid).pipe(take(1)).subscribe();
    });
  }

  deleteCollector(collector: Collector) {
    const modal = this.dialogService.open(DeleteConfirmModalComponent, {
      header: 'Confirm to delete',
      modal: true,
      closable: true,
      focusOnShow: false,
      dismissableMask: true,
      breakpoints: { '640px': '90vw' },
      data: collector.fingerprint || collector.guid,
    });

    modal.onClose.pipe(take(1)).subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.apiService.deleteCollector(this.caseMeta!.guid, collector.guid).pipe(take(1)).subscribe();
    });
  }

  deleteCollection(collection: Collection) {
    const modal = this.dialogService.open(DeleteConfirmModalComponent, {
      header: 'Confirm to delete',
      modal: true,
      closable: true,
      focusOnShow: false,
      dismissableMask: true,
      breakpoints: { '640px': '90vw' },
      data: collection.hostname || collection.guid,
    });

    modal.onClose.pipe(take(1)).subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.apiService.deleteCollection(this.caseMeta!.guid, collection.guid).pipe(take(1)).subscribe();
    });
  }
}
