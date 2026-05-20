import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';

import { AuthComponent } from './components/auth/auth.component';
import { AuthGuard } from './services/auth.guard';
import { CaseComponent } from './components/case/case.component';
import { ProfileComponent } from './components/profile/profile.component';

export const routes: Routes = [
  { path: 'login', component: AuthComponent, title: 'Helium - Authentication' },

  {
    path: '',
    canActivateChild: [AuthGuard],
    children: [
      { path: 'home', component: DashboardComponent, title: 'Helium - Dashboard' },
      { path: 'profiles', component: ProfileComponent, title: 'Helium - Profiles' },
      { path: 'case/:id', component: CaseComponent, title: 'Helium - Case' },
      { path: '**', redirectTo: '/home', pathMatch: 'full' },
    ],
  },

  { path: '**', redirectTo: '/login', pathMatch: 'full' },
];
