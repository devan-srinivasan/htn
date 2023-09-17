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
import logo from './logo.png';
// import gdrive from './gdrive_logo.png'
import style from './style.css'

function Header() {
  return (
    <>
      <Navbar className="navbarContainer"> 
        <Container>
        <img src={logo} className="App-logo" alt="logo"/>
          <Navbar.Brand className='Title'>eyenote.</Navbar.Brand>
          <Navbar.Brand className='subTitle'>see, learn, excel</Navbar.Brand>
        </Container>
      </Navbar>
      {/* <Navbar className="bg-body-tertiary justify-content-between"> */}

    {/* <Form className="formWrapper">
            <p className="formTitle">
                Log into 
                <img src={gdrive} className="drive-logo" alt="logo"/>
                Google Drive
            </p>
        <div class="form-group">
            <label for="exampleInputEmail1">Email address</label>
            <input type="email" class="form-control" id="exampleInputEmail1" aria-describedby="emailHelp" placeholder="Enter email"/>
        </div>
        <div class="form-group">
            <label for="exampleInputPassword1">Password</label>
            <input type="password" class="form-control" id="exampleInputPassword1" placeholder="Password"/>
        </div>
        
    </Form> */}

      {/* <Form inline>
        <Row>
          <Col xs="auto">
            <Form.Control
              placeholder="Username"
              aria-label="Username"
              aria-describedby="basic-addon1"
            />
          </Col>
          <Col xs="auto">
            <Form.Control
              placeholder="Password"
              aria-label="Password"
              aria-describedby="basic-addon2"
            />
          </Col>
          <Col xs="auto">
            <Button type="submit">Submit</Button>
          </Col>
        </Row>
      </Form> */}
    {/* </Navbar> */}
    </>
  );
}

export default Header;