import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { FloatLabelModule } from 'primeng/floatlabel';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TextareaModule } from 'primeng/textarea';
import { SkeletonModule } from 'primeng/skeleton';
import { FocusTrapModule } from 'primeng/focustrap';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ClipboardModule } from '@angular/cdk/clipboard';
import { MenuModule } from 'primeng/menu';
import { TooltipModule } from 'primeng/tooltip';
import { MessageModule } from 'primeng/message';
import { TabsModule } from 'primeng/tabs';
import { minimatch } from 'minimatch';
import { DialogService } from 'primeng/dynamicdialog';
import { SingleInputModalComponent } from '../../modals/single-input-modal/single-input-modal';
import { AddTargetModalComponent, AddTargetResult } from '../../modals/add-target-modal/add-target-modal';
import { forkJoin, take, from, concatMap, EMPTY } from 'rxjs';
import { DeleteConfirmModalComponent } from '../../modals/delete-confirm-modal/delete-confirm-modal.component';
import { ApiService } from '../../services/api.service';
import { HeliumProfile, HeliumRule, HeliumTarget } from '../../types/collect';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [
    FloatLabelModule,
    InputTextModule,
    ButtonModule,
    SelectModule,
    FormsModule,
    ReactiveFormsModule,
    TabsModule,
    TooltipModule,
    TextareaModule,
    FocusTrapModule,
    MessageModule,
    SkeletonModule,
    ClipboardModule,
    MenuModule,
    RouterLink,
  ],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.scss',
})
export class ProfileComponent implements OnInit {
  private api = inject(ApiService);
  dialogService = inject(DialogService);

  readonly opsystemOptions = ['windows', 'darwin', 'linux'];

  loading = signal<boolean>(true);
  searchPath = signal<string>('');
  selectedTargetId = signal<string | null>(null);
  selectedProfileId = signal<string | null>(null);
  opsystem = signal<string>('windows');

  profiles = signal<HeliumProfile[]>([]);
  targets = signal<HeliumTarget[]>([]);
  rules = signal<HeliumRule[]>([]);

  sortedProfiles = computed(() =>
    [...this.profiles()].sort((a, b) => {
      if (a.external !== b.external) return a.external ? -1 : 1;
      return a.name.localeCompare(b.name);
    }),
  );

  sortedTargets = computed(() =>
    [...this.targets()].sort((a, b) => {
      if (a.external !== b.external) return a.external ? -1 : 1;
      return b.rules.length - a.rules.length;
    }),
  );

  selectedProfile = computed(() => {
    const id = this.selectedProfileId();
    if (!id) return null;
    return this.profiles().find((p) => p.guid === id) || null;
  });

  filteredTargets = computed(() => {
    const profile = this.selectedProfile();
    const allTargets = this.sortedTargets();
    const baseTargets = profile ? allTargets.filter((t) => profile.targets.includes(t.guid)) : allTargets;

    const path = this.searchPath().trim();
    if (!path) return baseTargets;

    return baseTargets.filter(
      (target) =>
        target.name.toLowerCase().includes(path.toLowerCase()) ||
        target.rules.some((ruleGuid) => {
          const rule = this.rules().find((r) => r.guid === ruleGuid);
          return rule ? this.isGlobMatch(path, rule.glob) : false;
        }),
    );
  });

  selectedTarget = computed(() => {
    const id = this.selectedTargetId();
    return this.targets().find((t) => t.guid === id) || null;
  });

  displayRules = computed(() => {
    const target = this.selectedTarget();
    if (!target) return [];

    const path = this.searchPath().trim();
    return target.rules
      .map((ruleGuid) => this.rules().find((r) => r.guid === ruleGuid))
      .filter((r): r is HeliumRule => !!r)
      .map((rule) => ({ rule, matches: path ? this.isGlobMatch(path, rule.glob) : false }));
  });

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.loading.set(true);
    const os = this.opsystem();
    forkJoin({
      profiles: this.api.getHeliumProfiles(os),
      targets: this.api.getHeliumTargets(os),
      rules: this.api.getHeliumRules(os),
    }).subscribe({
      next: ({ profiles, targets, rules }) => {
        this.profiles.set(profiles);
        this.targets.set(targets);
        this.rules.set(rules);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  switchOpsystem(os: string) {
    this.opsystem.set(os);
    this.selectedProfileId.set(null);
    this.selectedTargetId.set(null);
    this.searchPath.set('');
    this.loadData();
  }

  selectProfile(guid: string) {
    if (this.selectedProfileId() === guid) {
      this.selectedProfileId.set(null);
    } else {
      this.selectedProfileId.set(guid);
    }
    this.selectedTargetId.set(null);
  }

  addProfile() {
    const modal = this.dialogService.open(SingleInputModalComponent, {
      header: 'Profile Name',
      modal: true,
      draggable: false,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '30vw',
      breakpoints: { '960px': '90vw' },
    })!;

    modal.onClose.pipe(take(1)).subscribe((name: string | null) => {
      if (!name) return;
      const os = this.opsystem();
      this.api.postHeliumProfile(os, { name }).subscribe((profile) => {
        this.profiles.update((ps) => [...ps, profile]);
        this.selectedProfileId.set(profile.guid);
      });
    });
  }

  renameProfile() {
    const profile = this.selectedProfile();
    if (!profile) return;

    const modal = this.dialogService.open(SingleInputModalComponent, {
      header: 'Profile Name',
      modal: true,
      draggable: false,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '30vw',
      breakpoints: { '960px': '90vw' },
      data: profile.name,
    })!;

    modal.onClose.pipe(take(1)).subscribe((name: string | null) => {
      if (!name) return;
      const os = this.opsystem();
      this.api.putHeliumProfile(os, profile.guid, { name }).subscribe((updated) => {
        this.profiles.update((ps) => ps.map((p) => (p.guid === updated.guid ? updated : p)));
      });
    });
  }

  deleteProfile() {
    const profile = this.selectedProfile();
    if (!profile) return;

    const modal = this.dialogService.open(DeleteConfirmModalComponent, {
      header: 'Confirm to delete',
      modal: true,
      draggable: false,
      closable: true,
      dismissableMask: true,
      breakpoints: { '640px': '90vw' },
      data: profile.name,
    })!;

    modal.onClose.pipe(take(1)).subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      const os = this.opsystem();
      this.api.deleteHeliumProfile(os, profile.guid).subscribe(() => {
        this.profiles.update((ps) => ps.filter((p) => p.guid !== profile.guid));
        this.selectedProfileId.set(null);
        this.selectedTargetId.set(null);
      });
    });
  }

  addTarget() {
    const profile = this.selectedProfile();
    const os = this.opsystem();

    if (!profile) {
      const modal = this.dialogService.open(SingleInputModalComponent, {
        header: 'Target Name',
        modal: true,
        draggable: false,
        appendTo: 'body',
        closable: true,
        dismissableMask: true,
        width: '30vw',
        breakpoints: { '960px': '90vw' },
      })!;

      modal.onClose.pipe(take(1)).subscribe((name: string | null) => {
        if (!name) return;
        this.api.postHeliumTarget(os, { name, rules: [] }).subscribe((target) => {
          this.targets.update((ts) => [...ts, target]);
          this.selectedTargetId.set(target.guid);
        });
      });
      return;
    }

    const modal = this.dialogService.open(AddTargetModalComponent, {
      header: 'Add Target to Profile',
      modal: true,
      draggable: false,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '35vw',
      breakpoints: { '960px': '90vw' },
      data: this.targets(),
    })!;

    modal.onClose.pipe(take(1)).subscribe((result: AddTargetResult | null) => {
      if (!result) return;

      if (result.action === 'reference') {
        const updatedTargets = [...profile.targets, result.targetGuid];
        this.api.putHeliumProfile(os, profile.guid, { targets: updatedTargets }).subscribe((updated) => {
          this.profiles.update((ps) => ps.map((p) => (p.guid === updated.guid ? updated : p)));
          this.selectedTargetId.set(result.targetGuid);
        });
      } else if (result.action === 'duplicate') {
        const source = this.targets().find((t) => t.guid === result.sourceGuid);
        const rules = source ? [...source.rules] : [];
        this.api.postHeliumTarget(os, { name: result.name, rules }).subscribe((newTarget) => {
          this.targets.update((ts) => [...ts, newTarget]);
          const updatedTargets = [...profile.targets, newTarget.guid];
          this.api.putHeliumProfile(os, profile.guid, { targets: updatedTargets }).subscribe((updated) => {
            this.profiles.update((ps) => ps.map((p) => (p.guid === updated.guid ? updated : p)));
          });
          this.selectedTargetId.set(newTarget.guid);
          requestAnimationFrame(() => {
            document
              .getElementById(`target-${newTarget.guid}`)
              ?.scrollIntoView({ behavior: 'smooth', block: 'center' });
          });
        });
      } else {
        this.api.postHeliumTarget(os, { name: result.name, rules: [] }).subscribe((newTarget) => {
          this.targets.update((ts) => [...ts, newTarget]);
          const updatedTargets = [...profile.targets, newTarget.guid];
          this.api.putHeliumProfile(os, profile.guid, { targets: updatedTargets }).subscribe((updated) => {
            this.profiles.update((ps) => ps.map((p) => (p.guid === updated.guid ? updated : p)));
          });
          this.selectedTargetId.set(newTarget.guid);
          requestAnimationFrame(() => {
            document
              .getElementById(`target-${newTarget.guid}`)
              ?.scrollIntoView({ behavior: 'smooth', block: 'center' });
          });
        });
      }
    });
  }

  removeTargetFromProfile(targetGuid: string) {
    const profile = this.selectedProfile();
    if (!profile) return;
    const os = this.opsystem();

    const updatedTargets = profile.targets.filter((t) => t !== targetGuid);
    this.api.putHeliumProfile(os, profile.guid, { targets: updatedTargets }).subscribe((updated) => {
      this.profiles.update((ps) => ps.map((p) => (p.guid === updated.guid ? updated : p)));
      if (this.selectedTargetId() === targetGuid) {
        this.selectedTargetId.set(null);
      }
    });
  }

  updateSearch(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    this.searchPath.set(value);

    const currentFiltered = this.filteredTargets();
    if (this.selectedTargetId() && !currentFiltered.some((p) => p.guid === this.selectedTargetId())) {
      this.selectedTargetId.set(null);
    }
  }

  selectTarget(guid: string) {
    this.selectedTargetId.set(guid);
  }

  addRuleToSelectedTarget() {
    const target = this.selectedTarget();
    if (!target) return;
    const os = this.opsystem();

    const modal = this.dialogService.open(SingleInputModalComponent, {
      header: 'Rule Glob',
      modal: true,
      draggable: false,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '30vw',
      breakpoints: { '960px': '90vw' },
    })!;

    modal.onClose.pipe(take(1)).subscribe((glob: string | null) => {
      if (!glob) return;
      this.api.postHeliumRule(os, { glob }).subscribe((newRule) => {
        this.rules.update((rs) => [...rs, newRule]);
        const updatedRules = [...target.rules, newRule.guid];
        this.api.putHeliumTarget(os, target.guid, { rules: updatedRules }).subscribe((updated) => {
          this.targets.update((ts) => ts.map((t) => (t.guid === updated.guid ? updated : t)));
        });
      });
    });
  }

  renameSelectedTarget() {
    const target = this.selectedTarget();
    if (!target) return;
    const os = this.opsystem();

    const modal = this.dialogService.open(SingleInputModalComponent, {
      header: 'Target Name',
      modal: true,
      draggable: false,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '30vw',
      breakpoints: { '960px': '90vw' },
      data: target.name,
    })!;

    modal.onClose.pipe(take(1)).subscribe((name: string | null) => {
      if (!name) return;
      this.api.putHeliumTarget(os, target.guid, { name }).subscribe((updated) => {
        this.targets.update((ts) => ts.map((t) => (t.guid === updated.guid ? updated : t)));
      });
    });
  }

  duplicateSelectedTarget() {
    const target = this.selectedTarget();
    if (!target) return;
    const profile = this.selectedProfile();
    const os = this.opsystem();

    const modal = this.dialogService.open(SingleInputModalComponent, {
      header: 'Target Name',
      modal: true,
      draggable: false,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '30vw',
      breakpoints: { '960px': '90vw' },
    })!;

    modal.onClose.pipe(take(1)).subscribe((name: string | null) => {
      if (!name) return;
      this.api.postHeliumTarget(os, { name, rules: [...target.rules] }).subscribe((newTarget) => {
        this.targets.update((ts) => [...ts, newTarget]);
        if (profile) {
          const updatedTargets = [...profile.targets, newTarget.guid];
          this.api.putHeliumProfile(os, profile.guid, { targets: updatedTargets }).subscribe((updated) => {
            this.profiles.update((ps) => ps.map((p) => (p.guid === updated.guid ? updated : p)));
          });
        }
        this.selectedTargetId.set(newTarget.guid);
        requestAnimationFrame(() => {
          document.getElementById(`target-${newTarget.guid}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
      });
    });
  }

  deleteSelectedTarget() {
    const target = this.selectedTarget();
    if (!target) return;
    const os = this.opsystem();

    const modal = this.dialogService.open(DeleteConfirmModalComponent, {
      header: 'Confirm to delete',
      modal: true,
      draggable: false,
      closable: true,
      dismissableMask: true,
      breakpoints: { '640px': '90vw' },
      data: target.name,
    })!;

    modal.onClose.pipe(take(1)).subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.api
        .deleteHeliumTarget(os, target.guid)
        .pipe(
          concatMap(() => {
            const affected = this.profiles().filter((p) => p.targets.includes(target.guid));
            if (!affected.length) return EMPTY;
            return from(affected).pipe(
              concatMap((p) =>
                this.api.putHeliumProfile(os, p.guid, {
                  targets: p.targets.filter((t) => t !== target.guid),
                }),
              ),
            );
          }),
        )
        .subscribe({
          next: (updated) => {
            this.profiles.update((ps) => ps.map((p) => (p.guid === updated.guid ? updated : p)));
          },
          complete: () => {
            this.targets.update((ts) => ts.filter((t) => t.guid !== target.guid));
            this.selectedTargetId.set(null);
          },
        });
    });
  }

  deleteRule(ruleGuid: string) {
    const target = this.selectedTarget();
    if (!target) return;
    const rule = this.rules().find((r) => r.guid === ruleGuid);
    if (!rule) return;
    const os = this.opsystem();

    const modal = this.dialogService.open(DeleteConfirmModalComponent, {
      header: 'Confirm to delete',
      modal: true,
      draggable: false,
      closable: true,
      dismissableMask: true,
      breakpoints: { '640px': '90vw' },
      data: rule.glob,
    })!;

    modal.onClose.pipe(take(1)).subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      const updatedRules = target.rules.filter((r) => r !== ruleGuid);
      this.api.putHeliumTarget(os, target.guid, { rules: updatedRules }).subscribe((updated) => {
        this.targets.update((ts) => ts.map((t) => (t.guid === updated.guid ? updated : t)));
      });
    });
  }

  isGlobMatch(path: string, glob: string): boolean {
    const normalizedPath = path.replace(/\\/g, '/');
    const normalizedGlob = glob.replace(/\\/g, '/');
    return minimatch(normalizedPath, normalizedGlob, {
      nocase: true,
      windowsPathsNoEscape: true,
    });
  }
}
