# **Policies Document**

## **Purpose**
This document defines the core policies and design principles for the application. These policies ensure clarity, consistency, and flexibility while addressing the needs of a desktop application designed for engineering and scientific analysis.

The policies are meant to:
1. **Guide Development**: Ensure consistent and maintainable development practices.
2. **Support Domain Needs**: Emphasize traceability, transparency, and scientific standards.
3. **Promote Flexibility**: Allow for future adaptations and framework independence.

As the project evolves, these policies will be updated to reflect new requirements and best practices.

---

## **General Principles**

### **1. Fail-Loud Design**
- **Immediate Feedback**: Errors and invalid inputs must trigger immediate user feedback via UI notifications or logs.
- **Actionable Errors**: All error messages must be descriptive, providing steps to resolve the issue.
- **Blocking Critical Failures**: Processing must halt if critical assumptions are violated or data is invalid.
- **Robustness**: If one component fails, the rest of the system must remain responsive and operational.

### **2. Transparency of Assumptions**
- **Assumption Disclosure**: Assumptions (e.g., default values, approximations) must be visible to users.
- **Override Options**: Users can override default assumptions through UI settings or configuration files.
- **Traceability**: All assumptions must be logged and included in reports for auditing purposes.

### **3. Framework Independence**
- **Core Logic Decoupling**: The core business logic must remain independent of GUI frameworks (e.g., PyQt).
- **Abstract Communication**: Use an abstraction layer for cross-layer communication to avoid framework lock-in.
- **Testable Logic**: All non-UI components must be testable independently of the chosen framework.

### **4. Modularity**
- **Single Responsibility**: Each component or module must have one clear responsibility.
- **Clear Interfaces**: Components must define clear input and output interfaces for maintainability and integration.
- **Reusability**: Components (e.g., visualization tools, sample managers) should be reusable across different parts of the application.
- **Plugin System**: Extend modularity to include a plugin system with clearly defined hooks for `before`, `on`, and `after` actions.

### **5. Data Integrity**
- **Minimize Conversions**: Limit unit conversions to reduce the accumulation of small uncertainties. Internally normalize data (e.g., `force` for Force) and apply conversions only for external use. Internal, units for all calculations.
- **Single Source of Truth**: Core data and parameters must have a single authoritative source. Calculations derived from these must be cached or recalculated, not duplicated.
- **Consistency**: Internal data and attributes must follow a consistent naming scheme, such as lowercase prefixes for units.
- **Thread-Safe State Management**: The application state must be accessible through thread-safe mechanisms to ensure data integrity.


---

## **Domain-Specific Policies**

### **1. Sample Management**
- **Lifecycle**: Raw data must remain unaltered, with derived datasets created for transformations.
- **Validation**: All samples must pass validation checks before being processed or stored.
- **Traceability**: Metadata must include details such as:
  - Creation date
  - Transformations applied
  - Assumptions used during processing

### **2. Analysis Standards**
- **Standards Compliance**: Users must select or define an analysis standard (e.g., ASTM, ISO) before running calculations.
- **Validation**: Inputs must comply with the selected standard; violations trigger warnings or errors.
- **Custom Configurations**: Users can override default standards, but deviations must be logged and highlighted.
- **Documentation**: Reports must specify the chosen standard and any deviations.

### **3. Data Preparation**
- **Raw Data Integrity**: Raw datasets must remain intact; transformations must create new derived datasets.
- **Outlier Handling**: Outliers must be flagged and excluded unless explicitly included by the user.
- **Zeroing**: Users can zero datasets against a baseline, with options to revert changes.
- **Grouping**: Sample groups must be created using clear, user-defined criteria.

### **4. Reporting**
- **Scientific Documentation**: Reports must include assumptions, data transformations, and traceability metadata.
- **Reproducibility**: Data and plots must be easily recreated through the scientific method. Reports should include detailed procedures and persistent data for auditability.
- **Export Formats**: Reports must support export to formats like PDF, Word, and Excel.

### **5. Error and Uncertainty**
- **Uncertainty Propagation**: Uncertainty values must propagate through calculations, with final results including cumulative uncertainty.
- **Error Visibility**: All errors must be immediately flagged and displayed in the UI or logs.
- **Visual Indicators**: Graphical outputs must include visual indicators of uncertainty (e.g., error bars).
- **Strcutured Logging**: File Logs must use structured formats (e.g., JSON) for easy parsing and analysis

---

## **Technical Policies**

### **1. Event Handling**
- **Framework-Specific Events**:  
  - Use the framework’s native event-handling mechanism (e.g., PyQt signals and slots) for internal communication within the same layer.
- **Unified Event Handler**:  
  - A centralized Event Handler must be used for cross-layer communication (e.g., frontend to backend).  
  - The Event Handler must log or notify all events for debugging and traceability.
- **Event Naming Conventions**:  
- Follow a standardized naming scheme for events:
  - **Action**: For trigger a behavior.
  - **State**: For updates stauts of a componet or actions.

### **2. Communication Between Layers**
- **Direct Communication**: Components in the same layer (e.g., frontend to frontend) must communicate directly, avoiding the Event Handler.
- **Isolation of Layers**: Frontend components must not directly access backend logic; all interactions must go through defined interfaces.

### **3. Visualization**
- **Customization**: Users must be able to customize visualizations (e.g., titles, axes, themes) through the UI.
- **Accessibility**: Visualizations must adhere to accessibility guidelines by defualt (e.g., high contrast, descriptive text).
- **Consistency**: Maintain consistent styling and labeling across all visualizations.
- **Export Options**: Visualizations must be exportable to formats like PNG, PDF, and SVG.

### **4. Data Flow and Integrity**
- **Validation on Input**: All input data must be validated before being processed.
- **Audit Trail**: Changes to data (e.g., outlier removal, adjustments) must be logged for traceability.
- **Structured Formats**: Data must be passed between components in structured formats (e.g., JSON, data classes).

---

## **Future Enhancements**
1. Extend policies for handling internationalization and localization.
2. Add detailed guidelines for performance optimization and scalability.
3. Define versioning and compatibility policies for future updates.
4. Frontend validation non domain specific, mainly ensure current types and all parms are pass. Back will be domain specific and should let frontend know if action is invalid
5. limit sources of truth (single copys of core data, parms to calculate dependents, cache calcultions). 
6. App state will be kept in the frontend
7. data and plots should be easily recarete (scientic method), go towards a detail procudre in the report and have the presisstant data. (Currenly plan to use a decrateive style for plots)

---

## **Version Control and Updates**
- Policies are versioned alongside the project codebase.
- Changes to policies must be documented in the `CHANGELOG.md` file.
- When updating policies:
  1. Ensure all affected modules comply with the new policy.
  2. Notify contributors of the changes and their rationale.
