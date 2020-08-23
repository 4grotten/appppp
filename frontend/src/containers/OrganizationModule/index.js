import React, {Component} from 'react';
import * as classnames from 'classnames';
import MobileTopHeader from '../../components/MobileTopHeader';
import TruncatedText from '../../components/UI/TruncatedText';
import DiscountSlider from '../../components/DicsountSlider';
import DiscountCard from '../../components/Cards/DiscountCard';
import ToggleButton from '../../components/UI/ToggleButton';
import {StandardButton} from '../../components/UI/Buttons';
import Linker from '../../components/UI/Linker';
import {checkForValidFile} from '../../common/helpers';
import OrganizationHeader from '../../components/OrganizationHeader';
import Preloader from '../../components/Preloader';
import PartnersStatistic from '../../components/PartnersStatistic';
import {ALLOWED_FORMATS, LINK_TYPES} from '../../common/constants';
import RowButton, {ROW_BUTTON_TYPES} from '../../components/UI/RowButton';
import MobileMenu from '../../components/MobileMenu';
import {setPreOrganization} from '../../store/actions/discountActions';
import {editDiscountImage, toggleShowContact} from '../../store/actions/organizationActions';
import {subscribeOrganization} from '../../store/actions/subscriptionActions';
import {uploadFile} from '../../store/actions/commonActions';
import {connect} from 'react-redux';
import Notify from '../../components/Notification';
import {Link} from 'react-router-dom';
import config from '../../config';
import {copyTextToClipboard} from '../../common/utils';
import {
  DiscountIcon,
  MarketIcon,
  PartnersIcon,
  QRIcon,
  ScanIcon,
  ShareIcon,
  EditIcon, MessageIcon
} from '../../components/UI/Icons';
import './index.scss';

const MENUS = ['Настройки', 'Инструменты', 'Обои'];

class OrganizationModule extends Component {
  state = {
    showMenu: false,
    selectedCard: null,
    cardImageLoading: false,
    menu: null,
  }

  toggleMenu = (menuState, menuID) => {
    this.setState({ ...this.state, showMenu: menuState, menu: menuID, selectedCard: null })
  }

  onCardEditClick = cardID => {
    this.setState({
      ...this.state,
      selectedCard: cardID,
      menu: 2,
      showMenu: true
    })
  }

  handleUpload = async e => {
    const file = e.target.files[0];
    const { selectedCard } = this.state;
    const { isValid } = checkForValidFile(file, ALLOWED_FORMATS);
    if (isValid && selectedCard) {
      try {
        this.setState({ ...this.state, cardImageLoading: true });
        const res = await this.props.uploadFile(file);
        if (res && res.id) {
          const editRes = await this.props.editDiscountImage(selectedCard, res.id, this.props.id);
          if (editRes && editRes.success) {
            return this.setState({ ...this.state, cardImageLoading: false, showMenu: false, menu: null, selectedCard: null });
          }

          Notify.info({ text: 'Не удалось загрузить изображение'});
          return this.setState({ ...this.state, cardImageLoading: false });
        }
      } catch (e) {
        return this.setState({ ...this.state, cardImageLoading: false, showMenu: false });
      }
    }
  }

  setCardBackground = async imageID => {
    const { selectedCard } = this.state;
    if (selectedCard) {
      const res = await this.props.editDiscountImage(selectedCard, imageID, this.props.id);
      if (res && res.success) {
        return this.setState({ ...this.state, cardImageLoading: false, showMenu: false, menu: null, selectedCard: null });
      }

      Notify.info({ text: 'Не удалось установить выбранное изображение'});
      return this.setState({ ...this.state, cardImageLoading: false, showMenu: false, selectedCard: null });
    }
  }

  render() {
    const { menu, showMenu } = this.state;
    const { id, user, orgDetail, history, toggleShowContact, onAddressClick, setPreOrganization, cardBackgrounds, subscribeOrganization } = this.props;
    const {data, loading} = orgDetail;

    if (loading) {
      return (
        <Preloader className="organization-module__preloader" />
      )
    }

    if (!data) {
      return null;
    }

    const { permissions, is_subscribed, currency } = data;

    return (
      <React.Fragment >
        <div className="organization-module">
          <MobileTopHeader
            onBack={() => history.goBack()}
            onMenu={() => this.toggleMenu(true, 1)}
            title={data.title && `@${data.title.toLowerCase()}` || ''}
            className="organization-module__top"
          />

          <div className="organization-module__content">
            <div className="container">
              <OrganizationHeader
                id={data.id}
                subscribers={data.subscribers}
                title={data.title}
                image={data.image}
                types={data.types}
                className="organization-module__header"
              />

              <Link className="organization-module__savings f-16" to={`/receipts?org=${data.id}&r=1`}>Ваша экономия: <span>{data.client_status && Math.floor(data.client_status.total_saved) || 0} {currency}</span></Link>

              <TruncatedText className="organization-module__description f-14">
                {data.description || ''}
              </TruncatedText>

              {data.address && ((data.full_location.latitude && data.full_location.longitude) ? (
                <button className="organization-module__address-btn f-14" onClick={onAddressClick}>{data.address}</button>
              )  : <p className="organization-module__address f-14 f-600">{data.address}</p>)}

              <div className={classnames("organization-module__contacts", data.show_contacts && "organization-module__contacts-show")}>
                {data.phone_numbers.map(phone => (
                  <Linker
                    key={phone.id}
                    type={LINK_TYPES.phone}
                    value={phone.phone_number}
                  />
                ))}

                {data.social_contacts.map(social => (
                  <Linker
                    key={social.id}
                    type={LINK_TYPES.web}
                    value={social.url}
                  />
                ))}
              </div>

              <div className="organization-module__tools row">
                <ToggleButton
                  label="Контакты и Web"
                  className="organization-module__contacts-btn"
                  toggled={data.show_contacts}
                  onClick={toggleShowContact}
                />

                {permissions && permissions.is_owner ? (
                  <StandardButton
                    label="Редактировать"
                    className="organization-module__edit-btn"
                    onClick={() => this.toggleMenu(true, 0)}
                  />
                ) : (
                  <StandardButton
                    label={is_subscribed ? "Отписаться" : "Подписаться"}
                    className={is_subscribed ? "organization-module__unsubscribe-btn" : "organization-module__subscribe-btn"}
                    onClick={() => subscribeOrganization(data.id)}
                  />
                )}
              </div>

              <div className="organization-module__cards">
                <div className="organization-module__card-cumulative">
                  <h2 className="organization-module__cards-title">Фиксированная карта</h2>
                  {!data.discounts.cumulative.length
                    ? permissions && permissions.is_owner ? <div>У вас нет фиксированных карт</div> :  <div>Нет фиксированных карт</div>
                    : (
                      <DiscountSlider className="organization-module__slider" clientStatus={data.client_status} cards={data.discounts.cumulative} >
                        {data.discounts.cumulative.map(card =>
                          <DiscountCard
                            key={card.id}
                            card={card}
                            clientStatus={data.client_status}
                            isOwner={permissions && permissions.can_edit_organization}
                            onEditClick={() => this.onCardEditClick(card.id)}
                            name={user && user.full_name}
                          />)}
                      </DiscountSlider>
                    )
                  }
                </div>

                <div className="organization-module__card-fixed">
                  <h2 className="organization-module__cards-title">Акционная карта</h2>
                  {!data.discounts.fixed.length
                    ? permissions.is_owner ? <div>У вас нет акционных карт</div> :  <div>Нет акционных карт</div>
                    : (
                      <DiscountSlider className="organization-module__slider" cards={data.discounts.fixed} >
                        {data.discounts.fixed.map(card =>
                          <DiscountCard
                            key={card.id}
                            card={card}
                            onEditClick={() => this.onCardEditClick(card.id)}
                            isOwner={permissions && permissions.is_owner}
                            name={user && user.full_name}
                          />)}
                      </DiscountSlider>
                    )
                  }
                </div>

                {permissions && permissions.can_see_stats && (
                  <PartnersStatistic
                    organization={data.id}
                    partners={data.partners}
                    className="organization-module__partners"
                  />
                )}

              </div>
            </div>
          </div>
        </div>

        <MobileMenu
          isOpen={showMenu}
          contentLabel={MENUS[menu]}
          onRequestClose={() => this.toggleMenu(false, null)}
        >
          <div className={classnames("organization-module__menu", showMenu && "organization-module__menu-active")}>
            {menu === 0 && permissions.is_owner && (
              <React.Fragment>
                <RowButton type={ROW_BUTTON_TYPES.link} label="Редактирование" showArrow={false} to={`${id}/edit-main`}>
                  <EditIcon />
                </RowButton>

                <RowButton type={ROW_BUTTON_TYPES.link} label="Управление скидками" showArrow={false} to={`${id}/edit-discounts`} >
                  <DiscountIcon />
                </RowButton>

                <RowButton type={ROW_BUTTON_TYPES.link} label="Партнеры" showArrow={false} to={`${id}/edit-partners`} >
                  <PartnersIcon />
                </RowButton>
              </React.Fragment>
            )}

            {menu === 1 && (
              <React.Fragment>
                {permissions && permissions.can_sale && (
                  <RowButton label="Провести скидки" showArrow={false} onClick={() => {
                    data && setPreOrganization({
                      id: data.id,
                      image: data.image,
                      title: data.title,
                      types: data.types,
                      currency: data.currency,
                    });
                    history.push(`/proceed-discount`);
                  }} >
                    <QRIcon />
                  </RowButton>
                )}

                {permissions && permissions.can_see_stats && (
                  <RowButton type={ROW_BUTTON_TYPES.link} label="Продажи и скидки" showArrow={false} to={`${id}/receipts`} >
                    <MarketIcon />
                  </RowButton>
                )}

                {permissions && permissions.can_send_message && (
                  <RowButton type={ROW_BUTTON_TYPES.link} label="Отправить сообщение подписчикам" showArrow={false} to={`${id}/messages`} >
                    <MessageIcon />
                  </RowButton>
                )}

                <RowButton type={ROW_BUTTON_TYPES.button} label="Поделиться" showArrow={false} onClick={async () => {
                  const shareUrl = `${config.baseURL}/organizations/${data && data.id}`;
                  const sharePayload = {
                    title: data && data.title,
                    text: data && data.description,
                    url: shareUrl,
                  }

                  try {
                    copyTextToClipboard(shareUrl, () => Notify.success({ text: 'Ссылка скопирована' }));
                    await navigator.share(sharePayload);
                  } catch (e) {}

                  this.toggleMenu(false, null);
                }}>
                  <ShareIcon />
                </RowButton>

                {permissions && !permissions.can_send_message && (
                  <RowButton type={ROW_BUTTON_TYPES.link} label="Сообщения подписчикам" showArrow={false} to={`/messages?org=${id}`} >
                    <MessageIcon />
                  </RowButton>
                )}

                {permissions && permissions.can_check_attendance && (
                  <RowButton type={ROW_BUTTON_TYPES.link} label="Сканер пропусков" showArrow={false} to={`${id}/attendance-scan`} >
                    <ScanIcon />
                  </RowButton>
                )}

                {permissions && permissions.can_edit_organization && (
                  <RowButton type={ROW_BUTTON_TYPES.link} label="Сотрудники" showArrow={false} to={`${id}/employees`} >
                    <PartnersIcon />
                  </RowButton>
                )}

                {permissions && permissions.can_edit_organization && (
                  <RowButton type={ROW_BUTTON_TYPES.link} label="Редактирование" showArrow={false} to={`${id}/edit-main`} >
                    <EditIcon />
                  </RowButton>
                )}

                {permissions && permissions.can_edit_organization && (
                  <RowButton type={ROW_BUTTON_TYPES.link} label="Управление скидками" showArrow={false} to={`${id}/edit-discounts`} >
                    <DiscountIcon />
                  </RowButton>
                )}

                {permissions && permissions.can_edit_partner && (
                  <RowButton type={ROW_BUTTON_TYPES.link} label="Управление партнерами" showArrow={false} to={`${id}/partners`} >
                    <PartnersIcon />
                  </RowButton>
                )}
              </React.Fragment>
            )}

            {menu === 2 && permissions.can_edit_organization && (
              <div className="discount-wallpaper">
                <form onSubmit={e => e.preventDefault()} className="discount-wallpaper__form">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M7.40972 0.100098L12.9233 0.101783C14.8672 0.122157 15.8489 0.330036 16.8666 0.874298C17.8382 1.39395 18.6062 2.16189 19.1258 3.13354C19.7003 4.20776 19.9 5.2419 19.9 7.40981V12.5904C19.9 14.7583 19.7003 15.7924 19.1258 16.8666C18.6062 17.8383 17.8382 18.6062 16.8666 19.1259C15.7923 19.7004 14.7582 19.9001 12.5903 19.9001H7.40972C5.24181 19.9001 4.20767 19.7004 3.13345 19.1259C2.1618 18.6062 1.39385 17.8383 0.874206 16.8666C0.299707 15.7924 0.100006 14.7583 0.100006 12.5904L0.101691 7.07676C0.122066 5.13293 0.329944 4.15123 0.874206 3.13354C1.39385 2.16189 2.1618 1.39395 3.13345 0.874298C4.20767 0.299799 5.24181 0.100098 7.40972 0.100098ZM13.0895 11.2917L9.36163 15.822C9.04614 16.2054 8.47975 16.2608 8.09587 15.9459L6.05405 14.271L3.24818 17.0266C3.46765 17.2234 3.71264 17.3944 3.98233 17.5386C4.67826 17.9108 5.35466 18.0665 6.84755 18.0951L7.40972 18.1001H12.5903L13.1525 18.0951C14.4697 18.0698 15.1513 17.9457 15.7715 17.6611L16.0177 17.5386C16.6757 17.1867 17.1867 16.6757 17.5385 16.0178C17.6384 15.8311 17.7226 15.6459 17.793 15.446L13.0895 11.2917ZM12.5903 1.9001H7.40972L6.84755 1.90508C5.5303 1.93035 4.84871 2.05451 4.2285 2.33905L3.98233 2.46156C3.32436 2.81345 2.81336 3.32445 2.46147 3.98242L2.33896 4.22859C2.01648 4.9315 1.90001 5.71323 1.90001 7.40981V12.5904L1.90499 13.1526C1.92672 14.2851 2.02154 14.9477 2.22853 15.5054L5.36937 12.4205C5.69735 12.0984 6.21538 12.0752 6.57081 12.3668L8.54271 13.9843L12.2919 9.42823C12.6155 9.03488 13.2009 8.98833 13.5827 9.32557L18.0914 13.3106C18.0928 13.2589 18.094 13.2063 18.095 13.1526L18.1 12.5904V7.40981L18.095 6.84764C18.0697 5.53039 17.9456 4.8488 17.6611 4.22859L17.5385 3.98242C17.1867 3.32445 16.6757 2.81345 16.0177 2.46156C15.3218 2.08938 14.6454 1.93372 13.1525 1.90508L12.5903 1.9001ZM6.50001 5.0001C7.32843 5.0001 8.00001 5.67167 8.00001 6.5001C8.00001 7.32853 7.32843 8.0001 6.50001 8.0001C5.67158 8.0001 5.00001 7.32853 5.00001 6.5001C5.00001 5.67167 5.67158 5.0001 6.50001 5.0001Z" fill="#3F8AE0"/>
                  </svg>

                  <label htmlFor="discount-image" className={classnames("discount-wallpaper__label f-17", this.state.cardImageLoading && "discount-wallpaper__label-loading")}>
                    {this.state.cardImageLoading ? 'Смена фона карты' : 'Сменить на свой фон'}
                  </label>
                  <input
                    type="file"
                    id="discount-image"
                    name="discount-image"
                    onChange={this.handleUpload}
                    disabled={this.state.cardImageLoading}
                  />
                </form>

                <div className="discount-wallpaper__recommendations">
                  <h6 className="f-16 f-600">Рекомендации</h6>
                  <ul className="discount-wallpaper__list">
                    {cardBackgrounds.loading && <div>Загрузка...</div>}
                    {cardBackgrounds.data && cardBackgrounds.data.map(bg => (
                      <li key={bg.id} className="discount-wallpaper__item" onClick={() => this.setCardBackground(bg.id)}>
                        <img src={bg.large} alt={bg.name}/>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </MobileMenu>
      </React.Fragment>
    );
  }
}

const mapStateToProps = state => ({
  user: state.userStore.user,
  orgDetail: state.organizationStore.orgDetail,
  cardBackgrounds: state.organizationStore.cardBackgrounds,
})

const mapDispatchToProps = dispatch => ({
  setPreOrganization: organization => dispatch(setPreOrganization(organization)),
  toggleShowContact: () => dispatch(toggleShowContact()),
  uploadFile: file => dispatch(uploadFile(file)),
  editDiscountImage: (cardID, imageID, orgID) => dispatch(editDiscountImage(cardID, imageID, orgID)),
  subscribeOrganization: orgID => dispatch(subscribeOrganization(orgID)),
})

export default connect(mapStateToProps, mapDispatchToProps)(OrganizationModule);