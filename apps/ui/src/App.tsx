import { useState } from "react";
import { clearToken, isLoggedIn, saveToken } from "./api/auth";
import { getUserInfo, isAdmin, UserInfo } from "./utils/tokenUtils";
import { Login } from "./pages/Login";
import { OtpVerify } from "./pages/OtpVerify";
import { Chat } from "./pages/Chat/index";
import { AccessDenied } from "./pages/AccessDenied";

type Step = "login" | "otp" | "app" | "access-denied";

function getInitialStep(): Step {
  if (!isLoggedIn()) return "login";
  if (!isAdmin()) return "access-denied";
  return "app";
}

export function App() {
  const [step, setStep] = useState<Step>(getInitialStep);
  const [phone, setPhone] = useState("");
  const [countryCode, setCountryCode] = useState("+91");
  const [userInfo, setUserInfo] = useState<UserInfo>(getUserInfo);

  const handleOtpSent = (p: string, cc: string) => {
    setPhone(p);
    setCountryCode(cc);
    setStep("otp");
  };

  const handleVerified = (token: string) => {
    saveToken(token);
    const info = getUserInfo();
    setUserInfo(info);
    if (isAdmin(info)) {
      setStep("app");
    } else {
      setStep("access-denied");
    }
  };

  const handleLogout = () => {
    clearToken();
    setPhone("");
    setUserInfo(getUserInfo());
    setStep("login");
  };

  if (step === "login") return <Login onOtpSent={handleOtpSent} />;
  if (step === "otp")
    return (
      <OtpVerify
        phone={phone}
        countryCode={countryCode}
        onVerified={handleVerified}
        onBack={() => setStep("login")}
      />
    );
  if (step === "access-denied")
    return <AccessDenied onLogout={handleLogout} userName={userInfo.name} />;

  return <Chat onLogout={handleLogout} userInfo={userInfo} />;
}
