<#import "template.ftl" as layout>
<#import "passkeys.ftl" as passkeys>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('username','password') displayInfo=realm.password && realm.registrationAllowed && !registrationDisabled??; section>
    <#if section = "header">
        ${msg("loginAccountTitle")}
    <#elseif section = "form">
        <#assign hasPasskey = enableWebAuthnConditionalUI?has_content>
        <#assign hasSocial = realm.password && social?? && social.providers?has_content>
        <#assign passwordOpen = !hasPasskey && !hasSocial
            || messagesPerField.existsError('username','password')
            || (login.username)?has_content>

        <div id="kc-form" class="m3-login-stack">
            <#-- 1. Passkey: the preferred way in. The base passkeys macro renders
                 #authenticateWebAuthnButton and wires up WebAuthn + conditional UI. -->
            <#if hasPasskey>
                <div class="m3-passkey-zone">
                    <@passkeys.conditionalUIData />
                    <p class="m3-passkey-hint">
                        <span class="m3-icon-check" aria-hidden="true"></span>${msg("m3PasskeyHint")}
                    </p>
                </div>
            </#if>

            <#-- 2. Identity providers: one round tonal button per provider. -->
            <#if hasSocial>
                <div id="kc-social-providers" class="m3-social">
                    <#if hasPasskey || realm.password>
                        <div class="m3-divider"><span>${msg("m3OrContinueWith")}</span></div>
                    </#if>
                    <ul class="m3-social-row">
                        <#list social.providers as p>
                            <li>
                                <a data-once-link data-disabled-class="m3-disabled" id="social-${p.alias}"
                                   class="m3-social-btn" href="${p.loginUrl}"
                                   title="${p.displayName!p.alias}" aria-label="${p.displayName!p.alias}">
                                    <img src="${url.resourcesPath}/img/providers/${p.alias?lower_case}.svg" alt=""
                                         onerror="this.onerror=null;this.src='${url.resourcesPath}/img/providers/oidc.svg'"/>
                                </a>
                            </li>
                        </#list>
                    </ul>
                </div>
            </#if>

            <#-- 3. Username & password: collapsed unless it is the only option
                 or the user is already interacting with it. -->
            <#if realm.password>
                <details class="m3-pass-details"<#if passwordOpen> open</#if>>
                    <summary<#if !hasPasskey && !hasSocial> class="m3-hidden"</#if>>
                        <span>${msg("m3PasswordToggle")}</span>
                        <span class="m3-icon-chevron" aria-hidden="true"></span>
                    </summary>

                    <form id="kc-form-login" class="m3-form" onsubmit="login.disabled = true; return true;" action="${url.loginAction}" method="post">
                        <#if !usernameHidden??>
                            <div class="m3-group">
                                <label for="username" class="m3-label"><#if !realm.loginWithEmailAllowed>${msg("username")}<#elseif !realm.registrationEmailAsUsername>${msg("usernameOrEmail")}<#else>${msg("email")}</#if></label>
                                <input tabindex="2" id="username" class="m3-input" name="username" value="${(login.username!'')}" type="text"
                                       autocomplete="${(enableWebAuthnConditionalUI?has_content)?then('username webauthn', 'username')}"
                                       aria-invalid="<#if messagesPerField.existsError('username','password')>true</#if>"
                                       dir="ltr"
                                />
                                <#if messagesPerField.existsError('username','password')>
                                    <span id="input-error" class="m3-error" aria-live="polite">
                                        ${kcSanitize(messagesPerField.getFirstError('username','password'))?no_esc}
                                    </span>
                                </#if>
                            </div>
                        </#if>

                        <div class="m3-group">
                            <label for="password" class="m3-label">${msg("password")}</label>
                            <div class="m3-input-group" dir="ltr">
                                <input tabindex="3" id="password" class="m3-input" name="password" type="password" autocomplete="current-password"
                                       aria-invalid="<#if messagesPerField.existsError('username','password')>true</#if>"
                                />
                                <button class="m3-pass-toggle" type="button" aria-label="${msg("showPassword")}"
                                        aria-controls="password" data-password-toggle tabindex="4"
                                        data-icon-show="m3-icon-eye" data-icon-hide="m3-icon-eye-off"
                                        data-label-show="${msg('showPassword')}" data-label-hide="${msg('hidePassword')}">
                                    <i class="m3-icon-eye" aria-hidden="true"></i>
                                </button>
                            </div>
                            <#if usernameHidden?? && messagesPerField.existsError('username','password')>
                                <span id="input-error" class="m3-error" aria-live="polite">
                                    ${kcSanitize(messagesPerField.getFirstError('username','password'))?no_esc}
                                </span>
                            </#if>
                        </div>

                        <div class="m3-form-row">
                            <#if realm.rememberMe && !usernameHidden??>
                                <label class="m3-check" for="rememberMe">
                                    <input tabindex="5" id="rememberMe" name="rememberMe" type="checkbox" class="m3-check-input"<#if login.rememberMe??> checked</#if>>
                                    <span class="m3-check-label">${msg("rememberMe")}</span>
                                </label>
                            <#else>
                                <span></span>
                            </#if>
                            <#if realm.resetPasswordAllowed>
                                <a tabindex="6" class="m3-link" href="${url.loginResetCredentialsUrl}">${msg("doForgotPassword")}</a>
                            </#if>
                        </div>

                        <div id="kc-form-buttons" class="m3-buttons">
                            <input type="hidden" id="id-hidden-input" name="credentialId" <#if auth.selectedCredential?has_content>value="${auth.selectedCredential}"</#if>/>
                            <input tabindex="7" class="m3-btn <#if hasPasskey>m3-btn-tonal<#else>m3-btn-filled</#if> m3-btn-block m3-btn-lg" name="login" id="kc-login" type="submit" value="${msg("doLogIn")}"/>
                        </div>
                    </form>
                </details>
                <script type="module" src="${url.resourcesPath}/js/passwordVisibility.js"></script>
            </#if>
        </div>
    <#elseif section = "info">
        <#if realm.password && realm.registrationAllowed && !registrationDisabled??>
            <div id="kc-registration">
                <span>${msg("noAccount")} <a tabindex="8" href="${url.registrationUrl}">${msg("doRegister")}</a></span>
            </div>
        </#if>
    </#if>

</@layout.registrationLayout>
