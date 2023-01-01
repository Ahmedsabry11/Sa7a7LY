// Import themes
import lightTheme from "./Theme/lightTheme";

// Import theme provider from styled components
import { ThemeProvider } from "styled-components";
import "./App.css";
import ImagesAndVideosTab from "./Components/ImagesAndVideosTab/ImagesAndVideosTab";
import submitAutoFiller from "./Services/submitAutoFiller";
import useFetchFunction from "./Hooks/useFetchFunction";
import BubbleSheet from "./Components/BubbleSheet/BubbleSheet";
import submitBubble from "./Services/submitBubble";
import Footer from "./Components/Footer/Footer";

function App() {
  const [data, error, isLoading, dataFetch] = useFetchFunction();
  /**
   * Function to handle submit the post
   * (Called when the user clicks on the submit button)
   */
  const handleSubmit = ({
    attachments = [],
    codesChoice,
    digitsChoice,
  } = {}) => {
    var bodyFormData = new FormData();
    attachments.forEach((element) => {
      bodyFormData.append("input", element, element.path);
    });
    bodyFormData.append("codesChoice", codesChoice);
    bodyFormData.append("digitsChoice", digitsChoice);
    submitAutoFiller(dataFetch, bodyFormData);
  };
  const handleSubmitBubble = ({ attachments = [] } = {}) => {
    var bodyFormData = new FormData();
    attachments.forEach((element) => {
      bodyFormData.append("input", element, element.path);
    });
    submitBubble(dataFetch, bodyFormData);
  };
  return (
    <div className="App">
      <ThemeProvider theme={lightTheme}>
        <ImagesAndVideosTab
          submitPost={handleSubmit}
          isLoadingSubmit={isLoading}
        />
        <BubbleSheet
          submitPost={handleSubmitBubble}
          isLoadingSubmit={isLoading}
        />
      </ThemeProvider>
      <Footer />
    </div>
  );
}

export default App;
