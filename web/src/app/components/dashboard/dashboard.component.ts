import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { MeterGroup } from 'primeng/metergroup';
import { MenuModule } from 'primeng/menu';
import { ApiService } from '../../services/api.service';
import { DialogService } from 'primeng/dynamicdialog';
import { CaseCreateModalComponent } from '../../modals/case-create-modal/case-create-modal.component';
import { CaseMetadata } from '../../types/case';
import { MenuItem } from 'primeng/api';
import { TooltipModule } from 'primeng/tooltip';
import { SkeletonModule } from 'primeng/skeleton';
import { UtilsService } from '../../services/utils.service';
import { DialogModule } from 'primeng/dialog';
import { debounceTime, Observable, take } from 'rxjs';
import { Info } from '../../types/API';
import { AsyncPipe, DatePipe } from '@angular/common';
import { DiskUsageModalComponent } from '../../modals/disk-usage-modal/disk-usage-modal.component';
import { FileSizePipe } from '../../shared/filesize.pipe';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { InputTextModule } from 'primeng/inputtext';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    RouterLink,
    CardModule,
    DatePipe,
    FileSizePipe,
    TooltipModule,
    ReactiveFormsModule,
    InputTextModule,
    MeterGroup,
    MenuModule,
    AsyncPipe,
    DialogModule,
    ButtonModule,
    SkeletonModule,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent {
  menuItems: MenuItem[] = [
    {
      label: 'Dark Mode',
      icon: 'pi pi-moon',
      command: () => this.utilsService.toggleDarkMode(),
    },
    {
      label: 'About',
      icon: 'pi pi-info-circle',
      command: () => (this.isAboutDialogVisible = true),
    },
    {
      label: 'Logout',
      icon: 'pi pi-sign-out',
      command: () => this.logout(),
    },
  ];
  info$: Observable<Info>;
  isAboutDialogVisible: boolean = false;
  frontendVersion: string;
  cases: CaseMetadata[] = [];
  displayedCases: CaseMetadata[] = [];
  searchInput = new FormControl('');
  emptyMeterGroup = [
    { label: 'Collectors', color: '#34d399', value: 0 },
    { label: 'Collections', color: '#0263b1', value: 0 },
    { label: 'Analyses', color: '#c084fc', value: 0 },
  ];

  constructor(
    private apiService: ApiService,
    private dialogService: DialogService,
    private utilsService: UtilsService,
  ) {
    this.info$ = this.apiService.getInfo();
    this.frontendVersion = this.utilsService.frontendVersion;

    this.apiService
      .getCases()
      .pipe(take(1))
      .subscribe({
        next: (cases) => {
          this.cases = cases.map((c) => {
            return { ...c, total: 0, quota: this.emptyMeterGroup };
          });
          this.cases.sort((a, b) => new Date(b.created as string).getTime() - new Date(a.created as string).getTime());
          this.updateDisplayedCases(this.cases);

          this.apiService
            .getDiskUsage()
            .pipe(take(1))
            .subscribe({
              next: (diskUsage) => {
                diskUsage.cases.forEach((c) => {
                  const total = c.analyses + c.collections + c.collectors;
                  const index = this.cases.findIndex((_c) => _c.guid == c.guid);
                  if (index > -1) {
                    this.cases[index].total = total;
                    this.cases[index].quota = [
                      {
                        label: 'Collectors',
                        color: '#34d399',
                        value: (c.collectors * 100) / total,
                      },
                      {
                        label: 'Collections',
                        color: '#0263b1',
                        value: (c.collections * 100) / total,
                      },
                      {
                        label: 'Analyses',
                        color: '#c084fc',
                        value: (c.analyses * 100) / total,
                      },
                    ];
                  }
                });
                this.updateDisplayedCases(this.cases);
              },
            });
        },
      });

    this.searchInput.valueChanges.pipe(debounceTime(250), takeUntilDestroyed()).subscribe({
      next: (value) => {
        this.updateDisplayedCases(this.cases, value || '');
      },
    });
  }

  openAddCaseModal() {
    const modal = this.dialogService.open(CaseCreateModalComponent, {
      header: 'Create Case',
      modal: true,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '30vw',
      breakpoints: {
        '960px': '90vw',
      },
    });

    modal.onClose.pipe(take(1)).subscribe((data: CaseMetadata | null) => {
      if (data)
        this.apiService
          .postCase(data)
          .pipe(take(1))
          .subscribe({
            next: (resp) => {
              this.cases = [...this.cases, { ...resp, total: 0, quota: this.emptyMeterGroup }];
              this.updateDisplayedCases(this.cases);
            },
          });
    });
  }

  diskUsageModal() {
    this.dialogService.open(DiskUsageModalComponent, {
      header: 'Disk Usage',
      modal: true,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '50vw',
      breakpoints: {
        '960px': '90vw',
      },
      data: this.cases,
    });
  }

  logout(): void {
    this.apiService.logout().pipe(take(1)).subscribe();
  }

  updateDisplayedCases(cases: CaseMetadata[], inputVal?: string): void {
    if (inputVal) {
      this.displayedCases = cases.filter(
        (c: CaseMetadata) =>
          c.name.toLowerCase().includes(inputVal.toLowerCase()) ||
          c.description?.toLowerCase().includes(inputVal.toLowerCase()) ||
          c.tsid?.toString().includes(inputVal),
      );
    } else {
      this.displayedCases = [...cases].sort((a, b) => {
        if (a.closed !== b.closed) return a.closed ? 1 : -1;
        return new Date(b.created!).getTime() - new Date(a.created!).getTime();
      });
    }
  }
}
