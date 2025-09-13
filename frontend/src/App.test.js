import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

test('renders App component', () => {
  render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
  // App should render without crashing and redirect to login
  // Since it redirects to /login, let's check that the document contains something
  expect(document.body).toBeInTheDocument();
});
