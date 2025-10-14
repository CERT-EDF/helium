import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { DatePickerModule } from 'primeng/datepicker';
import { DynamicDialogConfig, DynamicDialogRef } from 'primeng/dynamicdialog';
import { FloatLabelModule } from 'primeng/floatlabel';
import { InputTextModule } from 'primeng/inputtext';
import { TabsModule } from 'primeng/tabs';
import { TextareaModule } from 'primeng/textarea';
import { CheckboxModule } from 'primeng/checkbox';
import { ApiService } from '../../services/api.service';
import { FocusTrapModule } from 'primeng/focustrap';
import { MultiSelectModule } from 'primeng/multiselect';
import { SelectModule } from 'primeng/select';
import { take } from 'rxjs';

@Component({
  selector: 'app-collection-edit-modal',
  imports: [
    TabsModule,
    CardModule,
    FloatLabelModule,
    InputTextModule,
    ButtonModule,
    CheckboxModule,
    MultiSelectModule,
    SelectModule,
    DatePickerModule,
    ReactiveFormsModule,
    TextareaModule,
    FocusTrapModule,
  ],
  standalone: true,
  templateUrl: './collection-edit-modal.component.html',
  styleUrl: './collection-edit-modal.component.scss',
})
export class CollectionEditModalComponent {
  collectionForm: FormGroup;
  archs: string[] = [];
  opsystems: string[] = [];
  profiles: string[] = [];
  availableTags: string[] = [];

  constructor(
    private ref: DynamicDialogRef,
    private apiService: ApiService,
    private config: DynamicDialogConfig,
    private fb: FormBuilder,
  ) {
    this.collectionForm = this.fb.group({
      guid: '',
      tags: [],
      device: '',
      version: '',
      opsystem: null,
      hostname: '',
      fingerprint: '',
      collected: '',
      description: '',
    });

    this.apiService
      .getConstant()
      .pipe(take(1))
      .subscribe({
        next: (constant) => {
          this.archs = constant.enums.architecture;
          this.opsystems = constant.enums.opsystem;

          this.apiService
            .getAnalyzerInfos()
            .pipe(take(1))
            .subscribe({
              next: (analyzerInfos) => {
                this.availableTags = analyzerInfos.flatMap((info) => {
                  return info.tags;
                });
                this.availableTags.sort((a, b) => (a > b ? 1 : -1));

                const c = this.config.data;
                if (c.collection) {
                  this.collectionForm.patchValue({
                    ...c.collection,
                    collected: c.collection.collected ? new Date(c.collection.collected) : '',
                  });
                  if (
                    c.collection.tags.length == 0 &&
                    c.collection.opsystem &&
                    this.availableTags.includes(c.collection.opsystem)
                  )
                    this.collectionForm.get('tags')?.setValue([c.collection.opsystem]);
                  if (c.filename) this.collectionForm.get('description')?.setValue(c.filename);
                }
              },
            });
        },
      });
  }

  closeDialog() {
    let ret = this.collectionForm.value;
    this.ref.close(ret);
  }
}
