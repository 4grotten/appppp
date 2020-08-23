import React, {Component} from 'react';
import * as classnames from 'classnames';
import {readURL} from '../../common/helpers';
import {ALLOWED_FORMATS} from '../../common/constants';
import './index.scss';

class ImageUploader extends Component {
  async componentDidMount() {
    if (this.props.image) {
      try {
        const url = await readURL(this.props.image)
        this.setState({...this.state, previewUrl: url})
      } catch (e) {}
    }
  }

  constructor(props) {
    super(props);
    this.state = {
      file: null,
      previewUrl: props.imageURL
    }
  }

  onChange = async e => {
    const file = e.target.files[0];
    if (ALLOWED_FORMATS.includes(file.type)) {
      const previewUrl = await readURL(file);
      this.setState({ ...this.state, file, previewUrl});
      this.props.onChange(file, previewUrl);
    }
  }

  render() {
    const { className, error } = this.props;
    return (
      <div className={classnames("image-uploader", error && "image-uploader__error", className)}>
        {this.state.previewUrl && <img src={this.state.previewUrl} alt="Image preview" className="image-uploader__image"/>}
        <label htmlFor="image" className="image-uploader__label f-12 f-500" >{!this.state.previewUrl && 'Добавить Фото'}</label>
        <input type="file" name="image" id="image" onChange={this.onChange} />
      </div>
    );
  }
}

export default ImageUploader;