<?php
class Billet 
{
	protected 	$id;
	protected  	$image;
	protected  	$alt;
	protected  	$titre;
	protected  	$contenu;
	protected	$auteur;
	protected	$date_creation;
	protected	$date_creation_fr;
	 
	
	 
	 
	
public function hydrate(Array $values)
    {
        foreach ($values as $key=>$value)
        {
            $method = 'set' . ucfirst($key);
            if (method_exists($this, $method))
            {
                $this->$method($value);
            }
        }
    }	

 
	
	
// liste des getters
public function getId()
{
	return $this->id;
}
public function getImage()
{
	return $this->image;
}
public function getAlt()
{
	return $this->alt;
}
public function getTitre()
{
	return $this->titre;
}
public function getContenu()
{
	return $this->contenu;
}
public function getAuteur()
{
	return $this->auteur;
}
public function getDateCreation()
{
	return $this->date_creation;
}
public function getShortText()
{
	$text=substr($this->contenu, 0, 210 );
	
	return $text."..." ;
}

public function getShorterText($input, $length)
    {
        //no need to trim, already shorter than trim length
        if (strlen($input) <= $length) {
            return $input;
        }

        //find last space within length
        $last_space = strrpos(substr($input, 0, $length), ' ');
        if(!$last_space) $last_space = $length;
        $trimmed_text = substr($input, 0, $last_space);

        //add ellipses (...)
        $trimmed_text .= '...';

        return $trimmed_text;
    }
	
	/*add later??
	public function date_updated ()
{
	return $this->date_updated;
}
	public function is_publicated ()
{
	return $this->is_publicated;
}
*/
	
	
//Liste des setters
public function setId($id)
{
	 // On convertit l'argument en nombre entier.
    // Si c'en était déjà un, rien ne changera.
    // Sinon, la conversion donnera le nombre 0 (à quelques exceptions près, mais rien d'important ici).
    $id = (int) $id;
    
    // On vérifie ensuite si ce nombre est bien strictement positif.
    if ($id > 0)
    {
      // Si c'est le cas, c'est tout bon, on assigne la valeur à l'attribut correspondant.
      $this->id = $id;
    }
}
public function setImage($image)
  {
    if (is_string($image))
   
	{
		$this->image = $image;	
	}
  }
public function setAlt($alt)
  {
    if (is_string($alt))
   
	{
		$this->alt = $alt;	
	}
  }
public function setTitre($titre)
  {
    if (is_string($titre))
   
	{
		$this->titre = $titre;	
	}
  }
public function setContenu($contenu)
  {
    if (is_string($contenu))
   
	{
		$this->contenu = $contenu;	
	}
  }
public function setAuteur($auteur)
  {
    if (is_string($auteur))
   
	{
		$this->auteur = $auteur;	
	}
  }
public function setDateCreation($date_creation)
  {
    if (is_string($date_creation))
   
	{
		$this->date_creation = $date_creation;	
	}
  }
	 
	
	/*add later??
	public function setIs_publicated($value)
	{
		$this->is_publicated = $value;
	}
	*/
	
 }