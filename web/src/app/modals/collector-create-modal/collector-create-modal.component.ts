import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { DatePickerModule } from 'primeng/datepicker';
import { DynamicDialogRef } from 'primeng/dynamicdialog';
import { FloatLabelModule } from 'primeng/floatlabel';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TabsModule } from 'primeng/tabs';
import { TextareaModule } from 'primeng/textarea';
import { CheckboxModule } from 'primeng/checkbox';
import { ApiService } from '../../services/api.service';
import { FocusTrapModule } from 'primeng/focustrap';
import { MessageModule } from 'primeng/message';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { take } from 'rxjs';

@Component({
  selector: 'app-collector-create-modal',
  imports: [
    TabsModule,
    CardModule,
    FloatLabelModule,
    InputTextModule,
    ButtonModule,
    CheckboxModule,
    SelectModule,
    DatePickerModule,
    ReactiveFormsModule,
    TextareaModule,
    FocusTrapModule,
    MessageModule,
  ],
  standalone: true,
  templateUrl: './collector-create-modal.component.html',
  styleUrl: './collector-create-modal.component.scss',
})
export class CollectorCreateModalComponent {
  collectorForm: FormGroup;
  archs: string[] = [];
  opsystems: string[] = [];
  profiles: string[] = [];
  extra: { [key: string]: string[] } = {};
  extraEnabled: string[] = [];
  emptyProfiles: boolean = false;

  constructor(
    private ref: DynamicDialogRef,
    private apiService: ApiService,
    private fb: FormBuilder,
  ) {
    this.collectorForm = this.fb.group({
      guid: '',
      profile: null,
      arch: [null, Validators.required],
      opsystem: [null, Validators.required],
      device: ['', Validators.pattern(/^[a-zA-Z]:?$/)],
      memdump: [false, { disabled: true }],
      dont_be_lazy: [null, { disabled: true }],
      vss_analysis_age: [null, { disabled: true }],
      use_auto_accessor: [null, { disabled: true }],
      description: '',
    });

    this.apiService
      .getConstant()
      .pipe(take(1))
      .subscribe({
        next: (constant) => {
          this.archs = constant.enums.architecture;
          this.opsystems = constant.enums.opsystem;
          this.extra = constant.extra_fields;
        },
      });

    this.collectorForm
      .get('opsystem')
      ?.valueChanges.pipe(takeUntilDestroyed())
      .subscribe({
        next: (opsystem) => {
          if (!opsystem) return;
          this.apiService
            .getOpsystemProfiles(opsystem)
            .pipe(take(1))
            .subscribe({
              next: (profiles) => {
                this.emptyProfiles = false;
                if (!profiles.length) this.emptyProfiles = true;
                this.profiles = profiles.map((p) => p.name);
              },
            });

          // We disable the previously enabled fields
          if (this.extraEnabled.length) {
            this.extraEnabled.forEach((k) => {
              let c = this.collectorForm.get(k);
              c?.reset();
              c?.disable();
            });
            this.extraEnabled = [];
          }

          // If there are exrta fields, we enable them and store
          if (!this.extra.hasOwnProperty(opsystem)) return;
          let controls = this.collectorForm.controls;
          Object.values(this.extra[opsystem]).forEach((k) => {
            if (k in controls) {
              this.collectorForm.get(k)?.enable();
              this.extraEnabled.push(k);
            }
          });
        },
      });
  }

  closeDialog() {
    let ret = this.collectorForm.value;
    this.ref.close(ret);
  }
}
