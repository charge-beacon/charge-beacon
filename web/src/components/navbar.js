import Brand from "./brand";
import Form from "react-bootstrap/Form";
import BootstrapNavbar from 'react-bootstrap/Navbar';
import React from "react";

export default function Navbar() {
    return (
        <BootstrapNavbar expand="lg" fixed="top" className="bg-body-tertiary">
            <div className="w-100 px-3 d-flex flex-nowrap">
                <Brand/>
                <Form inline className="w-100">
                    <Form.Control
                        placeholder="Search for anything"
                        aria-label="Search"
                    />
                </Form>
            </div>
        </BootstrapNavbar>
    );
}