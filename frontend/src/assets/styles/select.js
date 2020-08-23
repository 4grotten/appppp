export const singleValueSelect = {
  option: (provided) => ({
    ...provided,
    cursor: 'pointer',
    fontSize: '14px',
    lineHeight: '20px',
    textTransform: 'capitalize',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis'
  }),
  placeholder: provided => ({
    ...provided,
    fontSize: '14px',
    lineHeight: '20px',
    color: '#818C99'
  }),
  control: (provided, state) => ({
    ...provided,
    borderRadius: 'unset',
    boxShadow: state.isFocused && 'unset',
    border: 'none',
    borderBottom: '1px solid #E6E6E6',
    borderColor: state.menuIsOpen && '#2C2D2E',
    '&:hover': {
      borderColor: '#E6E6E6'
    }
  }),
  valueContainer: provided => ({
    ...provided,
    padding: '0',
  }),
  singleValue: provided => ({
    ...provided,
    fontSize: '17px',
    lineHeight: '24px',
    color: '#2C2D2E',
    textTransform: 'capitalize'
  }),
  menu: provided => ({
    ...provided,
    overflow: 'hidden'
  }),
  menuList: provided => ({
    ...provided,
    '&::-webkit-scrollbar': {
      display: 'none'
    }
  }),
  indicatorSeparator: () => ({
    display: 'none'
  }),
  dropdownIndicator: (provided, { selectProps: { menuIsOpen } }) => ({
    ...provided,
    color: '#818C99',
    transform: menuIsOpen && 'rotate(180deg)',
    '& svg path': {
      fill: menuIsOpen && '#818C99'
    },
    '&:hover': { cursor: 'pointer' }
  })
};