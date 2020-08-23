import * as React from 'react';
import { Redirect } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import ForgotPage from './pages/ForgotPage';
import ProfilePage from './pages/ProfilePage';
import ProfileEditPage from './pages/ProfileEditPage';
import PageNotFound from './pages/PageNotFound';
import EditContactsPage from './pages/EditContactsPage';
import EditSocialsPage from './pages/EditSocialsPage';
import EditPasswordPage from './pages/EditPasswordPage';
import OrgCreatePage from './pages/OrgCreatePage';
import EditAuthNumberPage from './pages/EditAuthNumberPage';
import OrganizationDetailPage from './pages/OrganizationDetailPage';
import OrgEditMainPage from './pages/OrgEditMainPage';
import OrgEditDiscountPage from './pages/OrgEditDiscountPage';
import DiscountProceedPage from './pages/DiscountProceedPage';
import HomePage from './pages/HomePage';
import StatisticsPage from './pages/StatisticsPage';
import OrganizationsPage from './pages/OrganizationsPage';
import SubscriptionsPage from './pages/SubscriptionsPage';
import ReceiptsPage from './pages/ReceiptsPage';
import ReceiptDetailPage from './pages/ReceiptDetailPage';
import NotificationsPage from './pages/NotificicationsPage';
import ScanPage from './pages/ScanPage';
import OrgReceiptsPage from './pages/OrgReceiptsPage';
import OrgReceiptDetailPage from './pages/OrgReceiptDetailPage';
import OrgReceiptsByUserPage from './pages/OrgReceiptsByUserPage';
import SearchPage from './pages/SearchPage';
import EmployeesPage from './pages/EmployeesPage';
import EmployeeAddPage from './pages/EmployeeAddPage';
import RolesPage from './pages/RolesPage';
import RolesAddPage from './pages/RolesAddPage';
import RolesEditPage from './pages/RolesEditPage';
import AttendanceScanPage from './pages/AttendanceScanPage';
import MessagesPage from './pages/MessagesPage';
import MessageCreatePage from './pages/MessageCreatePage';
import EmployeeEditPage from './pages/EmployeeEditPage';
import SubscriptionMessagesPage from './pages/SubscriptionMessagesPage';
import OrgFollowersPage from './pages/OrgFollowersPage';
import OrgPartnerStatisticsPage from './pages/OrgPartnerStatisticsPage';
import OrgPartnersPage from './pages/OrgPartnersPage';
import PartnershipDetailPage from './pages/PartnershipDetailPage';
import AttendancePage from './pages/AttendancePage';

//TODO remove once launched
import DevPage from './pages/DevPage';

export const ROUTES = [
    {
        path: '/auth',
        component: LoginPage,
        exact: true,
        pageTitle: 'Authorization'
    },
    {
        path: '/forgot',
        component: ForgotPage,
        exact: true,
        pageTitle: 'Forgot Password'
    },
    {
        path: '/home',
        component: HomePage,
        exact: true,
        pageTitle: 'Home Page'
    },
    {
        path: '/home/search',
        component: SearchPage,
        exact: true,
        pageTitle: 'Search Organization'
    },
    {
        path: '/home/organizations',
        component: OrganizationsPage,
        exact: true,
        pageTitle: 'Organizations List Page'
    },
    {
        path: '/subscriptions',
        component: SubscriptionsPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Subscription Page'
    },
    {
        path: '/proceed-discount',
        component: DiscountProceedPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Discount Proceed'
    },
    {
        path: '/scan',
        component: ScanPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Scan Page'
    },
    {
        path: '/profile',
        component: ProfilePage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Profile Page'
    },
    {
        path: '/statistics',
        component: StatisticsPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Statistics Page'
    },
    {
        path: '/receipts',
        component: ReceiptsPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Receipts Page'
    },
    {
        path: '/receipts/:id',
        component: ReceiptDetailPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Receipt Detail Page'
    },
    {
        path: '/notifications/:mode',
        component: NotificationsPage,
        auth: token => !!token,
        exact: true,
        pageTitle: 'Notifications Page'
    },
    {
        path: '/profile/edit',
        component: ProfileEditPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Profile Edit Page'
    },
    {
        path: '/profile/edit-contacts',
        component: EditContactsPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Profile Edit Contacts Page'
    },
    {
        path: '/profile/edit-socials',
        component: EditSocialsPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Profile Edit Social Networks Page'
    },
    {
        path: '/profile/edit-auth/:code',
        component: EditAuthNumberPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Profile Edit Authorization number page'
    },
    {
        path: '/profile/edit-password',
        component: EditPasswordPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Profile Edit Password Page'
    },
    {
        path: '/messages',
        component: SubscriptionMessagesPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Subscription Messages Page'
    },
    {
        path: '/organizations/create',
        component: OrgCreatePage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Organizations Create Page'
    },
    {
        path: '/organizations/:id/attendance-scan',
        component: AttendanceScanPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Organizations Attendance Page'
    },
    {
        path: '/organizations/:id/partner-statistics',
        component: OrgPartnerStatisticsPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Organization Partner Statistics'
    },
    {
        path: '/organizations/:id/partners',
        component: OrgPartnersPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Organization Partners'
    },
    {
        path: '/organizations/:id/partners/:partnerID',
        component: PartnershipDetailPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Organization Partnership detail'
    },
    {
        path: '/organizations/:id/followers',
        component: OrgFollowersPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Employers Page'
    },
    {
        path: '/organizations/:id/employees',
        component: EmployeesPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Employers Page'
    },
    {
        path: '/organizations/:id/roles',
        component: RolesPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Roles Page'
    },
    {
        path: '/organizations/:id/employees/add',
        component: EmployeeAddPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Employee Add Page'
    },
    {
        path: '/organizations/:id/employees/:employeeID/attendance',
        component: AttendancePage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Employee Attendance Page'
    },
    {
        path: '/organizations/:id/employees/:employeeID',
        component: EmployeeEditPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Employee Add Page'
    },
    {
        path: '/organizations/:id/roles/add',
        component: RolesAddPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Roles Page'
    },
    {
        path: '/organizations/:id/roles/:roleID',
        component: RolesEditPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Roles Page'
    },
    {
        path: '/organizations/:id/edit-main',
        component: OrgEditMainPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Organization Edit Page'
    },
    {
        path: '/organizations/:id/edit-discounts',
        component: OrgEditDiscountPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Organization Edit Page'
    },
    {
        path: '/organizations/:id/receipts',
        component: OrgReceiptsPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Organization Receipts Page'
    },
    {
        path: '/organizations/:id/receipts-by/:userID',
        component: OrgReceiptsByUserPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Organization Receipts User Page'
    },
    {
        path: '/organizations/:id/receipts/:receiptID',
        component: OrgReceiptDetailPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Receipt Detail Page'
    },
    {
        path: '/organizations/:id/messages',
        component: MessagesPage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Messages Page'
    },
    {
        path: '/organizations/:id/messages/create',
        component: MessageCreatePage,
        exact: true,
        auth: token => !!token,
        pageTitle: 'Messages Create Page'
    },
    {
        path: '/organizations/:id',
        component: OrganizationDetailPage,
        exact: true,
        pageTitle: 'Organization Page'
    },
    {
        path: 'page-not-found',
        component: PageNotFound,
        exact: true,
        pageTitle: 'Not found'
    },
    {
        path: '/dev',
        component: () => <DevPage />,
        exact: true
    },
    {
        path: '/',
        render: () => <Redirect to="/home" />,
        exact: true
    },
    {
        path: '**',
        render: () => <Redirect to="/auth" />,
    }
]