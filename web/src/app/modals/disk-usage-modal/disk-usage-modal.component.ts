import { Component } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { DynamicDialogConfig, DynamicDialogRef } from 'primeng/dynamicdialog';
import { ApiService } from '../../services/api.service';
import { DiskUsage } from '../../types/API';
import { SkeletonModule } from 'primeng/skeleton';
import { FileSizePipe } from '../../shared/filesize.pipe';
import { CaseMetadata } from '../../types/case';
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { take } from 'rxjs';

type CaseWithDiskUsage = CaseMetadata & { du: DiskUsage };

@Component({
  selector: 'app-disk-usage-modal',
  imports: [ButtonModule, CardModule, TableModule, SkeletonModule, FileSizePipe],
  standalone: true,
  templateUrl: './disk-usage-modal.component.html',
  styleUrl: './disk-usage-modal.component.scss',
})
export class DiskUsageModalComponent {
  total: number = 0;
  cases: CaseWithDiskUsage[] = [];
  quota: number = 0;

  constructor(
    private ref: DynamicDialogRef,
    private apiService: ApiService,
    private config: DynamicDialogConfig,
  ) {
    this.cases = this.config.data.map((c: CaseMetadata) => {
      return {
        ...c,
        du: { guid: c.guid, analyses: 0, collections: 0, collectors: 0 },
      };
    });

    this.apiService
      .getConstant()
      .pipe(take(1))
      .subscribe({
        next: (constant) => (this.quota = constant.quota || 0),
      });

    this.apiService
      .getDiskUsage()
      .pipe(take(1))
      .subscribe({
        next: (diskUsage) => {
          diskUsage.cases.forEach((du) => {
            this.cases.find((c) => c.guid == du.guid)!.du = du;
            this.total += du.analyses + du.collections + du.collectors;
          });
        },
      });
  }

  closeDialog() {
    this.ref.close();
  }
}
