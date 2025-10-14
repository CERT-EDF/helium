import { Component } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { DynamicDialogConfig, DynamicDialogRef } from 'primeng/dynamicdialog';
import { ApiService } from '../../services/api.service';
import { CollectorSecret } from '../../types/collect';
import { SkeletonModule } from 'primeng/skeleton';
import { CardModule } from 'primeng/card';
import { ClipboardModule } from '@angular/cdk/clipboard';
import { UtilsService } from '../../services/utils.service';
import { TooltipModule } from 'primeng/tooltip';
import { take } from 'rxjs';

@Component({
  selector: 'app-collector-secrets-modal',
  imports: [ButtonModule, CardModule, SkeletonModule, ClipboardModule, TooltipModule],
  standalone: true,
  templateUrl: './collector-secrets-modal.component.html',
  styleUrl: './collector-secrets-modal.component.scss',
})
export class CollectorSecretsModalComponent {
  secrets?: CollectorSecret;

  constructor(
    private ref: DynamicDialogRef,
    private apiService: ApiService,
    private utilsService: UtilsService,
    private config: DynamicDialogConfig,
  ) {
    if (!this.config.data) {
      this.closeDialog();
    }

    this.apiService
      .getCaseCollectorSecrets(this.config.data.guid, this.config.data.collector)
      .pipe(take(1))
      .subscribe({
        next: (secrets) => (this.secrets = secrets),
      });
  }

  download(content: string, filename: string) {
    this.utilsService.toFileDownload(content, `${this.config.data.fingerprint}.${filename}`);
  }

  closeDialog() {
    this.ref.close();
  }
}
