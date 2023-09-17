// import Container from 'react-bootstrap/Container';
// import Nav from 'react-bootstrap/Nav';
// import Navbar from 'react-bootstrap/Navbar';
import Form from 'react-bootstrap/Form';
// import Button from 'react-bootstrap/Button';
// import InputGroup from 'react-bootstrap/InputGroup';
// import Row from 'react-bootstrap/Row';
// import Col from 'react-bootstrap/Col';
// import NavDropdown from 'react-bootstrap/NavDropdown';
// import 'bootstrap/dist/css/bootstrap.min.css';
// import logo from './logo.svg';
// // import gdrive from './gdrive_logo.png'
// import style from './style.css'
import { useNavigate } from 'react-router-dom';
import Header from '../Header';
import React, { useState, useEffect } from 'react';
import notif from './notif.png'
// import style from './style.css'
//Import socket
import io from "socket.io-client"



function Messages() {
    const [messages, setMessages] = useState([]);
    //Socket port
    // const socket_backend = io.connect("http://localhost:3001/",{transports: ['websocket'], secure: true, port: '3001'});

    const navigate = useNavigate();
  
    const handleClose = event => {
      event.preventDefault();
      navigate('/');
    }

    // setInterval(function() {
    //   fetch(`http://localhost:3001/llm-data`, {method: 'GET'})
    //   .then(response => response.json()).then(data => {
    //     if (data.length > 0) {
    //       setMessages([...messages, data['data']])
    //     }
    //   })
    // }, 10 * 1000); // 60 * 1000 milsec

    //Track data received from the server
    // useEffect(() => {
    //   socket_backend.on("llm-data", (data) => {
    //       console.log(data)
    //       //Get new message
    //       const new_message = JSON.loads(data)["model_response"]
    //       const updated_messages = [...messages, new_message]
    //       setMessages(updated_messages)
    //       // setMessdata["model_response"]
    //   })
    // })

    return (
    <>
      <Header/>
      <div className="messageWrapper">
        <img src={notif} className="notif" alt="notif"/> {" "}
        <p className="firstMessage"> Google Drive has been connected start double blinking to take notes!</p>
      </div>
      <div className="messages">
        {messages.map((item) => (
          <div className="messageWrapper">
          <img src={notif} className="notif" alt="notif"/>
          <p className="message"> {" "}{item}</p>
          </div>
        ))}
      </div>
      <div className="buttonWrapper">
      <Form className="formWrapper" onSubmit={handleClose}>
        <button type="submit" class="btn btn-primary end">
            End Session
      </button>
      </Form>
    </div>
    </>
  );
}

export default Messages;