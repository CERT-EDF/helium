import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { DynamicDialogRef } from 'primeng/dynamicdialog';
import { FormsModule } from '@angular/forms';
import { FloatLabelModule } from 'primeng/floatlabel';
import { SelectModule } from 'primeng/select';
import { ApiService } from '../../services/api.service';
import { take } from 'rxjs';

export interface CollectorTemplateResult {
  opsystem: string;
  arch: string;
}

@Component({
  selector: 'app-collector-template-modal',
  imports: [ButtonModule, FormsModule, FloatLabelModule, SelectModule],
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="px-4 flex flex-col gap-4 w-full">
      <p-floatlabel variant="in">
        <p-select
          inputId="opsystem"
          appendTo="body"
          [options]="opsystems()"
          [ngModel]="selectedOpsystem()"
          (ngModelChange)="selectedOpsystem.set($event)"
          fluid />
        <label for="opsystem">Operating System</label>
      </p-floatlabel>

      <p-floatlabel variant="in">
        <p-select
          inputId="arch"
          appendTo="body"
          [options]="archs()"
          [ngModel]="selectedArch()"
          (ngModelChange)="selectedArch.set($event)"
          fluid />
        <label for="arch">Architecture</label>
      </p-floatlabel>
    </div>
    <div class="mt-4 flex justify-end">
      <p-button
        text
        label="Download"
        icon="pi pi-download"
        [disabled]="!selectedOpsystem() || !selectedArch()"
        (click)="close()" />
    </div>
  `,
})
export class CollectorTemplateModalComponent {
  opsystems = signal<string[]>([]);
  archs = signal<string[]>([]);
  selectedOpsystem = signal<string | null>(null);
  selectedArch = signal<string | null>(null);

  constructor(
    private ref: DynamicDialogRef,
    private apiService: ApiService,
  ) {
    this.apiService
      .getConstant()
      .pipe(take(1))
      .subscribe((constant) => {
        this.opsystems.set(constant.enums.opsystem);
        this.archs.set(constant.enums.architecture);
      });
  }

  close() {
    const opsystem = this.selectedOpsystem();
    const arch = this.selectedArch();
    if (!opsystem || !arch) return;
    this.ref.close({ opsystem, arch } satisfies CollectorTemplateResult);
  }
}
