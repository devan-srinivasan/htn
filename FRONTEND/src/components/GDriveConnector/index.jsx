import Header from '../Header'
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import InputGroup from 'react-bootstrap/InputGroup';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import NavDropdown from 'react-bootstrap/NavDropdown';
import 'bootstrap/dist/css/bootstrap.min.css';
import gdrive from './gdrive_logo.png'
import {Link, Routes, Route, useNavigate} from 'react-router-dom';
import style from './style.css'


function DriveConnector() {

  const navigate = useNavigate();

  const handleSubmit = event => {
    event.preventDefault();
    fetch(`http://localhost:3001/auth-google`, {method: 'POST'})
    .then(response => {
      if (response.ok) {
        fetch(`http://localhost:3001/start-adhawk`, {method: 'POST'})
      }
    })
    .then(body => {
      console.log(body);
    }).then()

    navigate('/main');
  }

  return (
    <div>
      <Header />
      <Form className="formWrapper" onSubmit={handleSubmit}>
        <button type="submit" class="btn btn-primary">
          Connect to Google Drive
          <img src={gdrive} className="drive-logo" alt="logo"/>
      </button>
      </Form>
    </div>
  );
}

export default DriveConnector;
