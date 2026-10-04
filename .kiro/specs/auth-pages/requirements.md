# Requirements Document

## Introduction

This feature introduces a Login page and a Create Account (Sign Up) page for a web application styled after the SCORATES reference design. The UI uses a dark background with a split layout: left side for branding/welcome copy, right side for a dark card containing the form. User credentials are persisted in a local `users.json` file. The sign-up flow writes new users to that file; the login flow reads it to validate credentials. Both pages are linked to each other and a post-login success/home page is shown on successful authentication.

## Glossary

- **Auth_System**: The client-side authentication module responsible for reading/writing `users.json` and validating credentials.
- **Login_Page**: The HTML page containing the login form.
- **Signup_Page**: The HTML page containing the create account form.
- **Success_Page**: The page displayed after a successful login.
- **User_Store**: The `users.json` file that persists registered user records.
- **Credential**: A combination of email address and password used to authenticate a user.
- **Session**: A browser-side indicator (e.g. `sessionStorage` entry) that a user is authenticated.

---

## Requirements

### Requirement 1: Visual Design — Login Page

**User Story:** As a visitor, I want a visually styled login page that matches the SCORATES reference design, so that the product feels polished and on-brand.

#### Acceptance Criteria

1. THE Login_Page SHALL render on a dark background with a color value of `#000000` or equivalent near-black.
2. THE Login_Page SHALL display a top navigation bar containing the application name, navigation links (About, Help, Ask), and a right-side tagline.
3. THE Login_Page SHALL display the application name in the navbar where the first letter is rendered in a purple/magenta accent color and the remaining letters are rendered in white.
4. THE Login_Page SHALL render a two-column layout where the left column contains welcome/branding copy and the right column contains a dark card with the login form.
5. THE Login_Page SHALL display a "New to [App]? Create an account →" link in the left column that navigates to the Signup_Page.
6. THE Login_Page SHALL render the login form card with a heading styled in a purple-to-blue gradient, an email address input field, a password input field, a "Forgot password?" link, and a submit button styled in a bright magenta/pink color.
7. THE Login_Page SHALL apply a red/pink-toned border to the email and password input fields.
8. THE Login_Page SHALL display placeholder text "you@example.com" in the email input field and "Enter your password" in the password input field.
9. THE Login_Page SHALL be responsive such that on viewports narrower than 768px the two-column layout stacks into a single column.

---

### Requirement 2: Visual Design — Sign Up Page

**User Story:** As a new visitor, I want a sign-up page that matches the same visual style as the login page, so that the experience is consistent.

#### Acceptance Criteria

1. THE Signup_Page SHALL reuse the same dark background, navbar, two-column layout, and card styling defined for the Login_Page.
2. THE Signup_Page SHALL display a form card containing a Full Name input field, an Email Address input field, a Password input field, and a Confirm Password input field.
3. THE Signup_Page SHALL display a "Already have an account? Login →" link that navigates to the Login_Page.
4. THE Signup_Page SHALL display a submit button labeled "Create Account →" styled consistently with the Login_Page's submit button.
5. THE Signup_Page SHALL be responsive under the same breakpoint rules as the Login_Page.

---

### Requirement 3: User Store Structure

**User Story:** As a developer, I want a defined JSON file that stores user records, so that registration and login data persist between sessions.

#### Acceptance Criteria

1. THE Auth_System SHALL maintain a `users.json` file at the project root with a top-level `users` array.
2. THE User_Store SHALL store each user record as a JSON object containing the fields: `id` (unique string), `name` (string), `email` (string, lowercase), and `password` (string).
3. THE User_Store SHALL be initialized with an empty `users` array when no file exists.
4. WHEN the User_Store is read, THE Auth_System SHALL parse it as valid JSON and SHALL surface a descriptive error to the console if parsing fails.

---

### Requirement 4: Sign-Up Flow

**User Story:** As a new user, I want to register with my name, email, and password, so that I can create an account and later log in.

#### Acceptance Criteria

1. WHEN the user submits the sign-up form, THE Auth_System SHALL validate that the Full Name field is not empty.
2. WHEN the user submits the sign-up form, THE Auth_System SHALL validate that the Email Address field contains a value matching a standard email format (local-part@domain).
3. WHEN the user submits the sign-up form, THE Auth_System SHALL validate that the Password field contains at least 8 characters.
4. WHEN the user submits the sign-up form, THE Auth_System SHALL validate that the Confirm Password field value is identical to the Password field value.
5. IF any validation rule in criteria 1–4 fails, THEN THE Signup_Page SHALL display an inline error message adjacent to the failing field describing the specific validation failure, without submitting the form.
6. WHEN all validation rules pass and the submitted email already exists in the User_Store, THE Auth_System SHALL display an error message stating that an account with that email address already exists.
7. WHEN all validation rules pass and the submitted email does not exist in the User_Store, THE Auth_System SHALL write a new user record containing a generated unique `id`, the submitted `name`, the lowercase `email`, and the `password` to the User_Store.
8. WHEN a new user record is successfully written to the User_Store, THE Auth_System SHALL redirect the user to the Login_Page.

---

### Requirement 5: Login Flow

**User Story:** As a registered user, I want to log in with my email and password, so that I can access the application.

#### Acceptance Criteria

1. WHEN the user submits the login form, THE Auth_System SHALL validate that both the email and password fields are non-empty.
2. IF either the email or password field is empty, THEN THE Login_Page SHALL display an inline error message indicating that both fields are required.
3. WHEN the user submits the login form with non-empty fields, THE Auth_System SHALL read the User_Store and search for a record whose `email` matches the submitted email (case-insensitive).
4. WHEN a matching email record is found, THE Auth_System SHALL compare the submitted password against the stored `password` value for that record.
5. WHEN the email is not found in the User_Store, THE Auth_System SHALL display the error message "Invalid email or password." on the Login_Page.
6. WHEN the email is found but the password does not match, THE Auth_System SHALL display the error message "Invalid email or password." on the Login_Page.
7. WHEN the Credential is validated successfully, THE Auth_System SHALL create a Session entry in `sessionStorage` containing the authenticated user's `id` and `name`.
8. WHEN the Session is created, THE Auth_System SHALL redirect the user to the Success_Page.

---

### Requirement 6: Success / Home Page

**User Story:** As a logged-in user, I want to be shown a confirmation page after login, so that I know I have authenticated successfully.

#### Acceptance Criteria

1. THE Success_Page SHALL display a personalised welcome message using the authenticated user's name retrieved from the Session.
2. WHILE a valid Session exists, THE Success_Page SHALL remain accessible.
3. WHEN the Success_Page is loaded without a valid Session, THE Auth_System SHALL redirect the user to the Login_Page.
4. THE Success_Page SHALL provide a "Logout" action that clears the Session and redirects the user to the Login_Page.

---

### Requirement 7: Navigation Links Between Pages

**User Story:** As a user, I want clear navigation links between the login and sign-up pages, so that I can move between them without using the browser back button.

#### Acceptance Criteria

1. THE Login_Page SHALL display a visible link to the Signup_Page in both the left welcome column and accessible from the login card area.
2. THE Signup_Page SHALL display a visible link to the Login_Page.
3. WHEN a user clicks either inter-page link, THE Auth_System SHALL navigate to the target page without submitting any form data.

---

### Requirement 8: Error Message Accessibility

**User Story:** As a user with assistive technology, I want error messages to be accessible, so that I am informed of validation failures regardless of how I interact with the page.

#### Acceptance Criteria

1. THE Login_Page SHALL associate each inline error message with its corresponding input field using the `aria-describedby` attribute.
2. THE Signup_Page SHALL associate each inline error message with its corresponding input field using the `aria-describedby` attribute.
3. WHEN an error message is displayed, THE Auth_System SHALL set `aria-invalid="true"` on the corresponding input element.
4. WHEN an error message is cleared after correction, THE Auth_System SHALL remove the `aria-invalid` attribute from the corresponding input element.
