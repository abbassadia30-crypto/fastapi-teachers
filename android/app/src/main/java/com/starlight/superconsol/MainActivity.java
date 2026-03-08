package com.starlight.superconsol;
import android.os.Bundle;
import com.getcapacitor.BridgeActivity;
import io.capawesome.capacitorjs.plugins.firebase.authentication.FirebaseAuthenticationPlugin;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Manually register the plugin if auto-load fails
        registerPlugin(FirebaseAuthenticationPlugin.class);
    }
}