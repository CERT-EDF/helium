import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { DynamicDialogConfig, DynamicDialogRef } from 'primeng/dynamicdialog';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { InputTextModule } from 'primeng/inputtext';
import { FloatLabelModule } from 'primeng/floatlabel';

@Component({
  selector: 'app-single-input-modal',
  imports: [ButtonModule, ReactiveFormsModule, FormsModule, FloatLabelModule, InputTextModule],
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="px-4 w-full">
      <p-floatlabel variant="in">
        <input id="value" pInputText [(ngModel)]="value" fluid (keyup.enter)="close()" />
        <label for="value">Value</label>
      </p-floatlabel>
    </div>
    <div class="mt-2 flex justify-end">
      <p-button text [label]="isUpdate ? 'Update' : 'Create'" icon="pi pi-check" (click)="close()" />
    </div>
  `,
})
export class SingleInputModalComponent {
  value = signal<string>('');
  isUpdate: boolean;

  constructor(
    private ref: DynamicDialogRef,
    private config: DynamicDialogConfig,
  ) {
    const initial: string | undefined = this.config.data;
    if (initial) {
      this.value.set(initial);
      this.isUpdate = true;
    } else {
      this.isUpdate = false;
    }
  }

  close() {
    const value = this.value();
    if (!value) return;
    this.ref.close(value);
  }
}
