---
description:
globs:
alwaysApply: false
---
# Biblioperson Project Language Guidelines

## **Required Language Standards:**

- **All UI text, labels, and user-facing strings must be in English**
- **All code comments must be in English** 
- **All variable names, function names, and identifiers must be in English**
- **All API responses and error messages must be in English**
- **All documentation must be in English**

## **Examples of Correct Implementation:**

```typescript
// ✅ DO: Use English for all UI text
const button = "Delete Account";
const message = "This action cannot be undone";
const placeholder = "Enter your email";

// ✅ DO: Use English for component names and props
interface UserAccountProps {
  userName: string;
  deleteAccount: () => void;
}

// ✅ DO: Use English for error messages
throw new Error("Invalid email format");
```

## **Examples to Avoid:**

```typescript
// ❌ DON'T: Spanish in UI text
const button = "Eliminar Cuenta";
const message = "Esta acción no se puede deshacer";

// ❌ DON'T: Spanish in variable names
const nombreUsuario = "John";
const eliminarCuenta = () => {};

// ❌ DON'T: Spanish in comments
// Esta función elimina el usuario
function deleteUser() {}
```

## **Future Internationalization:**

- This is a temporary rule until i18n system is implemented
- All text will later use translation keys like `t('deleteAccount')`
- Keep UI text simple and translation-friendly
- Avoid complex concatenated strings

## **Implementation Notes:**

- Use consistent terminology throughout the app
- Prefer clear, simple English over complex phrases
- Follow standard UI/UX language patterns
- Test all user-facing text for clarity

## **Exceptions:**

- Chat communication with the user can remain in Spanish
- External API responses from third-party services
- User-generated content (uploaded documents, etc.)

---

**Remember:** This ensures consistency until we implement proper internationalization with translation keys.
