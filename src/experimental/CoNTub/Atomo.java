import java.awt.*;
import java.io.*;

class Atomo
{
	int tipo = 0;
	int selec = 0;
	String etiq = "  ";
	String pers = "  ";
	pto3D vert = null;
	Color color = null;
	double r = 0;		//de doubles
	int mconec[];
	int mconecA[];		//array de conec alternativas (para newzmat)
	tabPe TablaP;

	  Atomo ()
	{
		vert = new pto3D (0.0, 0.0, 0.0);
		tipo = 0;
		r = 0.0;
		selec = 0;
		color = Color.black;
		etiq = "  ";
		pers = "  ";
		mconec = new int[10];
		  mconecA = new int[10];
		  TablaP = tabPe.getInstance();

	}

	Atomo (int t, int s, String e, String p, pto3D pto, Color c, double radio)
	{
		tipo = t;
		etiq = e;
		pers = p;
		vert = pto.clona ();
		color = c;
		r = radio;
		mconec = new int[10];
		mconecA = new int[10];
		TablaP = tabPe.getInstance();

	}

	Atomo (pto3D p, int t)
	{
		TablaP = tabPe.getInstance();
		tipo = t;
		vert = p.clona ();
		etiq = TablaP.getSimbolo (t);
		pers = "  ";
		color = TablaP.getColor (t);
		r = TablaP.getSize (t);
		mconec = new int[10];
		mconecA = new int[10];

	}

	Atomo (pto3D p, int t, Color c)
	{
		TablaP = tabPe.getInstance();
		tipo = t;
		vert = p.clona ();
		etiq = TablaP.getSimbolo (t);
		pers = "  ";
		color = c;
		r = TablaP.getSize (t);
		mconec = new int[10];
		mconecA = new int[10];

	}
//LISTA DE METODOS BASICOS!!!



}
