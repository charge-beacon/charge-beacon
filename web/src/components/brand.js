import Navbar from 'react-bootstrap/Navbar';
import { ReactComponent as LogoLight } from './Logo_Text_Charge_Beacon_Light_Theme.svg';

function Brand() {
    return (
        <Navbar.Brand href="#home" className="d-flex align-items-center">
            <LogoLight height={28} width="auto" alt="Charge Beacon app" />
        </Navbar.Brand>
    );
}

export default Brand;
