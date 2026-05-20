import { ChangeDetectionStrategy, Component, computed, signal } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { DynamicDialogConfig, DynamicDialogRef } from 'primeng/dynamicdialog';
import { FormsModule } from '@angular/forms';
import { InputTextModule } from 'primeng/inputtext';
import { FloatLabelModule } from 'primeng/floatlabel';
import { SelectModule } from 'primeng/select';
import { HeliumTarget } from '../../types/collect';

export type AddTargetResult =
  | { action: 'reference'; targetGuid: string }
  | { action: 'duplicate'; sourceGuid: string; name: string }
  | { action: 'blank'; name: string };

@Component({
  selector: 'app-add-target-modal',
  imports: [ButtonModule, FormsModule, FloatLabelModule, InputTextModule, SelectModule],
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="px-4 flex flex-col gap-4">
      <p-floatlabel variant="in" class="w-full">
        <p-select
          inputId="existing"
          [options]="existingTargets"
          [ngModel]="selectedTarget()"
          (ngModelChange)="selectedTarget.set($event)"
          optionLabel="name"
          [showClear]="true"
          appendTo="body"
          fluid />
        <label for="existing">Existing target (optional)</label>
      </p-floatlabel>

      <p-floatlabel variant="in" class="w-full">
        <input
          id="name"
          pInputText
          [ngModel]="newName()"
          (ngModelChange)="newName.set($event)"
          fluid
          (keyup.enter)="close()" />
        <label for="name">{{
          isReferenceOnly() ? 'Name (not needed for reference)' : 'New name (optional for clone)'
        }}</label>
      </p-floatlabel>

      @if (hint()) {
        <p class="text-xs text-primary-600 font-medium -mt-2">{{ hint() }}</p>
      }
    </div>
    <div class="mt-2 flex justify-end">
      <p-button text [label]="actionLabel()" icon="pi pi-check" [disabled]="!canSubmit()" (click)="close()" />
    </div>
  `,
})
export class AddTargetModalComponent {
  existingTargets: HeliumTarget[];
  selectedTarget = signal<HeliumTarget | null>(null);
  newName = signal<string>('');

  constructor(
    private ref: DynamicDialogRef,
    private config: DynamicDialogConfig,
  ) {
    this.existingTargets = (this.config.data as HeliumTarget[]) ?? [];
  }

  isReferenceOnly = computed(() => !!this.selectedTarget() && !this.newName().trim());
  canSubmit = computed(() => !!this.selectedTarget() || !!this.newName().trim());

  actionLabel = computed(() => {
    if (this.selectedTarget() && this.newName().trim()) return 'Duplicate';
    if (this.selectedTarget()) return 'Reference';
    return 'Create';
  });

  hint = computed(() => {
    const sel = this.selectedTarget();
    const name = this.newName().trim();
    if (sel && name) return `Will duplicate "${sel.name}" as "${name}" and add to profile.`;
    if (sel) return `Will reference the existing target "${sel.name}" in this profile.`;
    if (name) return `Will create a blank target named "${name}".`;
    return '';
  });

  close() {
    if (!this.canSubmit()) return;

    const sel = this.selectedTarget();
    const name = this.newName().trim();
    let result: AddTargetResult;

    if (sel && name) {
      result = { action: 'duplicate', sourceGuid: sel.guid, name };
    } else if (sel) {
      result = { action: 'reference', targetGuid: sel.guid };
    } else {
      result = { action: 'blank', name };
    }
    this.ref.close(result);
  }
}
