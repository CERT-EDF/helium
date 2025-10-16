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
import { FocusTrapModule } from 'primeng/focustrap';
import { PasswordModule } from 'primeng/password';
import { ApiService } from '../../services/api.service';
import { take } from 'rxjs';

@Component({
  selector: 'app-collector-import-modal',
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
    PasswordModule,
  ],
  standalone: true,
  templateUrl: './collector-import-modal.component.html',
  styleUrl: './collector-import-modal.component.scss',
})
export class CollectorImportModalComponent {
  collectorSecretForm: FormGroup;
  arch: string[] = [];
  opsystem: string[] = [];

  constructor(
    private apiService: ApiService,
    private ref: DynamicDialogRef,
    private fb: FormBuilder,
  ) {
    this.apiService
      .getConstant()
      .pipe(take(1))
      .subscribe({
        next: (constant) => {
          this.arch = constant.enums.architecture;
          this.opsystem = constant.enums.opsystem;
        },
      });

    this.collectorSecretForm = this.fb.group({
      arch: [null, Validators.required],
      opsystem: [null, Validators.required],
      secret: ['', Validators.required],
      key_pem: ['', Validators.required],
      fingerprint: ['', Validators.required],
      description: '',
    });
  }

  onPrivateKeyUpload(event: Event): void {
    const input = event.target as HTMLInputElement;

    if (input.files && input.files.length == 1) {
      const file = input.files[0];
      const reader = new FileReader();

      reader.onload = (e) => {
        this.collectorSecretForm.get('fingerprint')?.setValue(file.name.split('.')[0]);
        this.collectorSecretForm.get('key_pem')?.setValue(e.target?.result as string);
      };

      reader.onerror = (e) => {
        console.error('Error reading privatekey file:', e);
      };

      reader.readAsText(file);
    }
  }

  closeDialog() {
    let ret = this.collectorSecretForm.value;
    this.ref.close(ret);
  }
}
