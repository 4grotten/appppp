import * as React from 'react';
import * as classnames from 'classnames';
import AvatarEditor from 'react-avatar-editor'
import {RotateIcon} from '../Icons';
import {dataURItoBlob} from '../../../common/utils';
import './index.scss';

export const cropAvatar = editorRef => {
  try {
    const canvasScaled = editorRef.getImageScaledToCanvas().toDataURL('image/jpeg');
    const imageBlob = dataURItoBlob(canvasScaled);
    const formData = new FormData();
    formData.append('file', imageBlob, `avatar_${new Date().toISOString()}.jpg`);
    return formData;
  } catch (e) {
    console.warn('Could not resolve image');
    return null;
  }
}

class AvatarEdit extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      scale: 1,
      rotate: 0
    };
  }

  rotate = () => {
    this.setState({...this.state, rotate: this.state.rotate + 90})
  }

  setEditorRef = editor => {
    this.props.setFieldValue('editorRef', editor);
  }

  render() {
    const {src, error} = this.props;
    return (
      <div className={classnames("avatar-edit__container", error && "avatar-edit__error")}>
        <AvatarEditor
          ref={this.setEditorRef}
          image={src}
          width={132}
          height={132}
          border={0}
          color={[255, 255, 255, 0.6]} // RGBA
          scale={this.state.scale}
          rotate={this.state.rotate}
          className="avatar-edit"
        />
        <RotateIcon onClick={this.rotate} className="avatar-edit__rotate" />
        <div />
      </div>
    )
  }
}

export default AvatarEdit;