const org = {
  id: 53,
  title: 'Fanta',
  image: {
    id: 125,
    file: 'http://91.236.120.118/media/common/file/avatar2_NsK05Up.jpg',
    name: 'avatar2_NsK05Up.jpg'
  },
  subscribers: 0,
  description: 'Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.',
  currency: 'XCD',
  show_contacts: false,
  opens_at: '09:00:00',
  closes_at: '18:00:00',
  address: 'ул. Суперская 254',
  full_location: {
    latitude: 42.8731328,
    longitude: 74.62832019999999
  },
  types: [
    {
      id: 737,
      title: 'It компания'
    }
  ],
  phone_numbers: [
    {
      id: 17,
      phone_number: '+996312313123'
    },
    {
      id: 18,
      phone_number: '+996555948484'
    },
    {
      id: 19,
      phone_number: '+996702434543'
    }
  ],
  social_contacts: [
    {
      id: 9,
      url: 'https://trello.com/b/WcDLJBzb/power-frontenders'
    },
    {
      id: 10,
      url: 'https://www.instagram.com/detskiysad_otadoya/?hl=en'
    },
    {
      id: 11,
      url: 'www.mamboo.com'
    },
    {
      id: 12,
      url: 'https://www.facebook.com/urmat.djanybaev/posts/3970390746379609'
    }
  ],
  discounts: {
    cumulative: [
      {
        id: 33,
        type: 'cumulative',
        percent: 15,
        limit: '5000.00',
        currency: 'XCD',
        image: null,
        organization_id: 53
      },
      {
        id: 34,
        type: 'cumulative',
        percent: 25,
        limit: '10000.00',
        currency: 'XCD',
        image: null,
        organization_id: 53
      },
      {
        id: 35,
        type: 'cumulative',
        percent: 50,
        limit: '50000.00',
        currency: 'XCD',
        image: null,
        organization_id: 53
      }
    ],
    fixed: [
      {
        id: 30,
        type: 'fixed',
        percent: 10,
        limit: null,
        currency: null,
        image: null,
        organization_id: 53
      },
      {
        id: 31,
        type: 'fixed',
        percent: 15,
        limit: null,
        currency: null,
        image: null,
        organization_id: 53
      },
      {
        id: 32,
        type: 'fixed',
        percent: 20,
        limit: null,
        currency: null,
        image: null,
        organization_id: 53
      }
    ]
  },
  saved_amount: 0,
  is_subscribed: false,
  permissions: {
    is_owner: true,
    can_sale: true,
    can_check_attendance: true,
    can_see_stats: true,
    can_edit_organization: true
  },
  active_card: {
    cumulative: 33,
    sum: 93000,
    next: 100000
  }
}