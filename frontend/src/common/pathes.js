export default class Pathes {
  static Auth = class {
    static authenticate = 'register_auth/';
    static verifyCode = 'verify_code/';
    static resendCode = 'resend_code/';
    static login = 'login/';
    static logout = 'logout/';
    static setPassword = 'set_password/';
    static changePassword = 'users/doChangePassword/';
    static forgotPassword = 'users/forgot_password/';
    static validateOldNumber = 'users/doValidateOldNumber/';
    static sendCodeToNewNumber = 'users/doSendCode/';
    static doChangeAndVerifyNewNumber = 'users/doChangeAndVerifyNewNumber/';
  };

  static Profile = class {
    static update = 'init_profile/';
    static get = 'users/me/';
    static phones = user_id => `users/${user_id}/phone_numbers/`;
    static setPhones = 'users/phone_numbers/';
    static socials =  user_id => `users/${user_id}/social_networks/`;
    static setSocials = 'users/social_networks/';
  };

  static Organization = class {
    static create = 'organizations/';
    static list = 'organizations/';
    static get = (orgID) => `organizations/${orgID}/`;
    static edit = (orgID) => `organizations/${orgID}/`;
    static setPhones = (orgID) => `organizations/${orgID}/phone_numbers/`;
    static setSocials = (orgID) => `organizations/${orgID}/social_networks/`;
    static types = 'organization_types/';
    static discounts = 'discounts/';
    static createDiscount = 'discounts/';
    static bulkUpdateDiscounts = 'discounts/doBulkUpdate/';
    static bulkDeleteDiscounts = 'discounts/doBulkDelete/';
    static cardBackgrounds = 'discount_backgrounds/';
    static discountImage = cardID => `discounts/${cardID}/`;
    static subscribe = `subscriptions/`;
    static receipts = `transactions/`;
    static receiptDetail = id => `transactions/${id}/`;
    static followers = id => `/organizations/${id}/followers/`;
  };

  static Subscriptions = class {
    static getList = '/subscriptions/'
  }

  static Common = class {
    static currency = 'countries/'
  }

  static File = class {
    static upload = 'files/';
  };

  static Discount = class {
    static preprocess = 'transactions/preprocess/';
    static completeTransaction = 'transactions/complete/';
  };

  static Home = class {
    static homeOrganizations = 'homepage/organizations/';
    static orgsByCategories = 'categorized_organizations/';
    static localBanners = 'homepage/banner_info/';
    static getCategoryDetail = id => `categories/${id}/`;
    static search = 'homepage/search/';
  };

  static Statistics = class {
    static allStatistics = 'statistics/organizations/';
    static summary = 'statistics/totals/';
    static orgSummary = orgID => `statistics/${orgID}/totals/`;
    static receipts = 'statistics/transactions/';
    static receiptDetail = id => `statistics/transactions/${id}/`;
    static getOrgTitle = id => `organizations/${id}/getOrganizationTitle/`;
    static partnerStatistics = orgID => `statistics/${orgID}/partners_totals/`;
  };

  static Notifications = class {
    static notifications = 'notifications/';
    static settings = 'notifications/settings/';
    static count = 'notifications/statistics/';
    static FCM = 'devices/';
  };

  static Employees = class {
    static list = 'employees/';
    static info = id => `employees/user_info/${id}/`;
    static roles = 'roles/';
    static roleDetail = id => `roles/${id}/`;
    static addEmployee = 'employees/';
    static employee = id => `employees/${id}/`;
    static transferOwnership = 'employees/doTransferOwnership/';
  };

  static Messages = class {
    static organization = orgID => `organizations/${orgID}/messages/`;
    static subscriptionMSG = 'messages/';
    static orgRecipientsCount = orgID => `organizations/${orgID}/getFollowersCount/`;
  };

  static Partners = class {
    static partners = id => `organizations/${id}/partners/`;
    static partnerships = id => `organizations/${id}/partnerships/`;
    static partnershipDetail = id => `partnerships/${id}/`;
    static createPartnership = 'partnerships/';
  };

  static Attendance = class {
    static info = 'attendance/user_info/';
    static attendance = 'attendance/';
    static stats = employeeID => `employees/${employeeID}/attendance/`;
  };
}